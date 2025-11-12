"""
Alert management service for Schengen compliance monitoring (Phase 3.6.4).

Responsibilities:
- Calculate rolling 90/180-day usage per employee.
- Persist alert metadata to the SQLite `alerts` table.
- Provide helper APIs for querying and resolving alerts.
- Optional daily scheduler + email notifications.
"""

from __future__ import annotations

import logging
import os
import smtplib
from contextlib import contextmanager
from datetime import date
from email.message import EmailMessage
from typing import Any, Dict, Iterable, List, Optional, Tuple

from flask import current_app, has_app_context

from app.models import get_db
from app.services.rolling90 import presence_days, days_used_in_window

logger = logging.getLogger(__name__)


ALERT_THRESHOLDS = {
    "YELLOW": 75,
    "ORANGE": 85,
    "RED": 90,
}

ALERT_PRIORITY = {"RED": 3, "ORANGE": 2, "YELLOW": 1}


@contextmanager
def _db_conn(existing=None):
    """Context manager that yields a SQLite connection and commits on exit."""
    should_close = False
    if existing is not None:
        conn = existing
    elif has_app_context():
        conn = get_db()
    else:
        import sqlite3

        db_path = os.getenv("DATABASE_PATH", "data/eu_tracker.db")
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        should_close = True
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        if should_close:
            try:
                conn.close()
            except Exception:  # pragma: no cover - defensive cleanup
                pass


def _determine_risk(days_used: int) -> Optional[str]:
    if days_used >= ALERT_THRESHOLDS["RED"]:
        return "RED"
    if days_used >= ALERT_THRESHOLDS["ORANGE"]:
        return "ORANGE"
    if days_used >= ALERT_THRESHOLDS["YELLOW"]:
        return "YELLOW"
    return None


def _format_usage_summary(days_used: int, limit: int = 90) -> Tuple[str, int]:
    days_remaining = limit - days_used
    if days_remaining >= 0:
        summary = f"{days_used}/{limit} days used ({days_remaining} remaining)"
    else:
        summary = f"{days_used}/{limit} days used ({abs(days_remaining)} over limit)"
    return summary, days_remaining


def _calculate_employee_usage(conn, employee_id: int) -> Optional[Dict[str, Any]]:
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM employees WHERE id = ?", (employee_id,))
    row = cursor.fetchone()
    if row is None:
        return None

    employee_name = row["name"]
    cursor.execute(
        "SELECT entry_date, exit_date, country FROM trips WHERE employee_id = ?",
        (employee_id,),
    )
    trips = [dict(r) for r in cursor.fetchall()]

    today = date.today()
    presence = presence_days(trips)
    days_used = days_used_in_window(presence, today)
    summary, days_remaining = _format_usage_summary(days_used)

    risk = _determine_risk(days_used)
    return {
        "employee_name": employee_name,
        "days_used": days_used,
        "days_remaining": days_remaining,
        "risk_level": risk,
        "message": f"{employee_name} has {summary}.",
    }


def check_alert_status(employee_id: int) -> Optional[str]:
    """
    Recalculate alert state for the given employee.

    Returns the active risk level ("RED"/"ORANGE"/"YELLOW") or None when compliant.
    """
    with _db_conn() as conn:
        usage = _calculate_employee_usage(conn, employee_id)
        if usage is None:
            logger.debug("No employee found for alert check (id=%s)", employee_id)
            return None

        risk = usage["risk_level"]
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, risk_level FROM alerts WHERE employee_id = ? AND resolved = 0",
            (employee_id,),
        )
        existing = cursor.fetchone()

        if risk is None:
            if existing:
                cursor.execute(
                    "UPDATE alerts SET resolved = 1 WHERE id = ?",
                    (existing["id"],),
                )
                logger.info(
                    "Alert resolved for employee %s (%s)",
                    employee_id,
                    usage["employee_name"],
                )
            return None

        message = usage["message"]
        if existing:
            if existing["risk_level"] != risk:
                cursor.execute(
                    """
                    UPDATE alerts
                    SET risk_level = ?, message = ?, created_at = CURRENT_TIMESTAMP,
                        resolved = 0, email_sent = 0
                    WHERE id = ?
                    """,
                    (risk, message, existing["id"]),
                )
                logger.info(
                    "Alert level updated for employee %s → %s",
                    employee_id,
                    risk,
                )
            else:
                cursor.execute(
                    "UPDATE alerts SET message = ? WHERE id = ?",
                    (message, existing["id"]),
                )
        else:
            cursor.execute(
                """
                INSERT INTO alerts (employee_id, risk_level, message, resolved, email_sent)
                VALUES (?, ?, ?, 0, 0)
                """,
                (employee_id, risk, message),
            )
            logger.info(
                "Alert created for employee %s → %s",
                employee_id,
                risk,
            )

        return risk


def refresh_all_alerts() -> None:
    """Recalculate alert status for every employee."""
    with _db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM employees")
        employee_ids = [row["id"] for row in cursor.fetchall()]

    for employee_id in employee_ids:
        try:
            check_alert_status(employee_id)
        except Exception:
            logger.exception("Failed to refresh alert for employee %s", employee_id)


def get_active_alerts(risk_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    risk_filter_normalized = risk_filter.upper() if isinstance(risk_filter, str) else None
    with _db_conn() as conn:
        cursor = conn.cursor()
        query = """
            SELECT a.id,
                   a.employee_id,
                   a.risk_level,
                   a.message,
                   a.created_at,
                   a.email_sent,
                   e.name AS employee_name
            FROM alerts AS a
            LEFT JOIN employees AS e ON e.id = a.employee_id
            WHERE a.resolved = 0
        """
        params: List[Any] = []
        if risk_filter_normalized in ALERT_PRIORITY:
            query += " AND a.risk_level = ?"
            params.append(risk_filter_normalized)

        query += """
            ORDER BY CASE a.risk_level
                        WHEN 'RED' THEN 3
                        WHEN 'ORANGE' THEN 2
                        WHEN 'YELLOW' THEN 1
                        ELSE 0
                     END DESC,
                     a.created_at DESC
        """
        cursor.execute(query, params)
        rows = cursor.fetchall()

    alerts: List[Dict[str, Any]] = []
    with _db_conn() as conn:
        for row in rows:
            usage = _calculate_employee_usage(conn, row["employee_id"])
            alerts.append(
                {
                    "id": row["id"],
                    "employee_id": row["employee_id"],
                    "employee_name": usage["employee_name"] if usage else row["employee_name"],
                    "risk_level": row["risk_level"],
                    "message": usage["message"] if usage else row["message"],
                    "created_at": row["created_at"],
                    "email_sent": row["email_sent"],
                    "days_used": usage["days_used"] if usage else None,
                    "days_remaining": usage["days_remaining"] if usage else None,
                }
            )
    return alerts


def resolve_alert(alert_id: int) -> bool:
    with _db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE alerts SET resolved = 1 WHERE id = ? AND resolved = 0",
            (alert_id,),
        )
        updated = cursor.rowcount
    return updated > 0


def mark_alerts_emailed(alert_ids: Iterable[int]) -> None:
    alert_ids = list(alert_ids)
    if not alert_ids:
        return
    with _db_conn() as conn:
        cursor = conn.cursor()
        cursor.executemany(
            "UPDATE alerts SET email_sent = 1 WHERE id = ?",
            [(alert_id,) for alert_id in alert_ids],
        )


def _format_email_body(alerts: List[Dict[str, Any]]) -> str:
    lines = [
        "Daily Schengen Compliance Alerts",
        "================================",
        "",
    ]
    for alert in alerts:
        days_remaining = alert.get("days_remaining")
        if days_remaining is None:
            detail = ""
        elif days_remaining >= 0:
            detail = f"{days_remaining} days remaining"
        else:
            detail = f"{abs(days_remaining)} days over limit"
        lines.append(
            f"- {alert['employee_name']}: {alert['days_used']}/90 days used "
            f"→ {alert['risk_level']} risk ({detail})"
        )
    lines.append("")
    lines.append("This message was generated automatically by ComplyEUR.")
    return "\n".join(lines)


def _send_email(recipient: str, subject: str, body: str) -> bool:
    host = os.getenv("SMTP_HOST") or os.getenv("MAIL_SERVER")
    port = int(os.getenv("SMTP_PORT") or os.getenv("MAIL_PORT") or 587)
    username = os.getenv("SMTP_USERNAME") or os.getenv("MAIL_USERNAME")
    password = os.getenv("SMTP_PASSWORD") or os.getenv("MAIL_PASSWORD")
    use_tls = (os.getenv("SMTP_USE_TLS") or "true").lower() in {"1", "true", "yes"}
    from_address = (
        os.getenv("SMTP_FROM_ADDRESS")
        or os.getenv("MAIL_DEFAULT_SENDER")
        or username
        or "alerts@complyeur.local"
    )

    if not host:
        logger.warning("SMTP host not configured; skipping email dispatch.")
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = from_address
    message["To"] = recipient
    message.set_content(body)

    try:
        with smtplib.SMTP(host, port, timeout=15) as server:
            if use_tls:
                server.starttls()
            if username and password:
                server.login(username, password)
            server.send_message(message)
        logger.info("Alert email sent to %s", recipient)
        return True
    except Exception:
        logger.exception("Failed to send alert email to %s", recipient)
        return False


def send_pending_alert_emails() -> int:
    """Send a summary email for alerts that have not yet triggered a notification."""
    admin_email = (
        os.getenv("ADMIN_EMAIL")
        or current_app.config.get("ADMIN_EMAIL")
        or current_app.config.get("CONFIG", {}).get("ADMIN_EMAIL")
    )
    if not admin_email:
        logger.debug("ADMIN_EMAIL not configured; skipping alert email.")
        return 0

    alerts = [
        alert
        for alert in get_active_alerts()
        if alert.get("email_sent") in (0, False, None)
    ]
    if not alerts:
        return 0

    subject = "ComplyEUR Schengen compliance alerts"
    body = _format_email_body(alerts)
    if _send_email(admin_email, subject, body):
        mark_alerts_emailed(alert["id"] for alert in alerts)
        return len(alerts)
    return 0


def start_alert_scheduler(app) -> None:
    """
    Start background scheduler to refresh alerts daily and send notifications.
    Skips scheduler when running in testing mode or when explicitly disabled.
    """
    def _initial_refresh():
        with app.app_context():
            refresh_all_alerts()
            send_pending_alert_emails()

    if (
        app.config.get("TESTING")
        or app.config.get("CONFIG", {}).get("TEST_MODE")
        or os.getenv("DISABLE_ALERT_SCHEDULER") == "1"
    ):
        logger.info("Alert scheduler disabled (testing/test mode).")
        _initial_refresh()
        return

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
    except Exception:
        logger.warning("APScheduler not available; skipping alert scheduler.")
        _initial_refresh()
        return

    scheduler = BackgroundScheduler(timezone="UTC")

    def _run_daily():
        with app.app_context():
            refresh_all_alerts()
            send_pending_alert_emails()

    scheduler.add_job(
        _run_daily,
        trigger="interval",
        hours=24,
        id="daily_alert_check",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Alert scheduler started (24h interval).")

    # Run an initial refresh shortly after startup to populate alerts
    _initial_refresh()

    def _shutdown():
        try:
            scheduler.shutdown(wait=False)
        except Exception:  # pragma: no cover - best effort
            pass

    import atexit

    atexit.register(_shutdown)
