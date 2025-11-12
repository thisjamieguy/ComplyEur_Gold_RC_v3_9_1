from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional, Tuple

from flask import Flask, render_template, session, url_for, request

# Ensure the main ComplyEur package is importable when running from the sandbox
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import load_config  # noqa: E402


def _resolve_database_path() -> str:
    """Return the absolute path to the ComplyEur SQLite database."""
    relative_path = os.getenv("CALENDAR_DEV_DB", "data/eu_tracker.db")
    db_path = Path(relative_path)
    if not db_path.is_absolute():
        db_path = PROJECT_ROOT / db_path
    return str(db_path)


def create_app() -> Flask:
    """Create a minimal Flask app exposing only the calendar stack."""
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
    )

    config_data = load_config()

    app.config.update(
        SECRET_KEY=os.getenv("CALENDAR_DEV_SECRET_KEY", "calendar-dev-sandbox-key"),
        DATABASE=_resolve_database_path(),
        CONFIG=config_data,
        FUTURE_JOB_WARNING_THRESHOLD=int(
            os.getenv(
                "CALENDAR_DEV_WARNING_THRESHOLD",
                config_data.get("FUTURE_JOB_WARNING_THRESHOLD", 80),
            )
        ),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=False,
        WTF_CSRF_ENABLED=False,
        CALENDAR_DEV_AUTO_ADMIN=os.getenv("CALENDAR_DEV_AUTO_ADMIN", "1") == "1",
    )

    from app.models import get_db, init_db  # noqa: E402
    from app.routes_calendar import bp as calendar_api_bp  # noqa: E402

    # Ensure core tables are present for sandbox usage.
    with app.app_context():
        try:
            init_db()
        except Exception as exc:  # pragma: no cover - defensive
            app.logger.warning("Calendar sandbox could not initialise DB: %s", exc)

    app.register_blueprint(calendar_api_bp)

    if app.config["CALENDAR_DEV_AUTO_ADMIN"]:

        @app.before_request
        def _ensure_admin_session() -> None:
            """Provide an auto-authenticated session for local sandbox work."""
            session.setdefault("user_id", 1)
            session.setdefault("user_role", "admin")

    @app.teardown_appcontext
    def _close_connection(exception: Optional[BaseException]) -> None:  # pragma: no cover
        """Close SQLite connections opened during the request lifecycle."""
        from flask import g

        conn = getattr(g, "_db_conn", None)
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
            finally:
                if getattr(g, "_db_conn", None) is conn:
                    try:
                        delattr(g, "_db_conn")
                    except AttributeError:
                        g._db_conn = None

    def _lookup_employee(employee_id: int) -> Optional[Tuple[int, str]]:
        """Fetch employee metadata to mirror the main ComplyEur view."""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name FROM employees WHERE id = ?",
                (employee_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return int(row["id"]), row["name"]
        except Exception:
            return None

    @app.route("/")
    def calendar_home():
        """Expose the calendar template without the rest of the ComplyEur UI shell."""
        focus_employee_id = ""
        focus_employee_name = ""

        raw_employee_id = request.args.get("employee_id", "").strip()
        if raw_employee_id:
            try:
                employee_id = int(raw_employee_id)
                match = _lookup_employee(employee_id)
                if match:
                    focus_employee_id = str(match[0])
                    focus_employee_name = match[1]
            except ValueError:
                pass

        splash_image = None
        splash_path = BASE_DIR / "static" / "images" / "me_construction.png"
        if splash_path.exists():
            splash_image = url_for("static", filename="images/me_construction.png")

        return render_template(
            "calendar.html",
            warning_threshold=app.config.get("FUTURE_JOB_WARNING_THRESHOLD", 80),
            focus_employee_id=focus_employee_id,
            focus_employee_name=focus_employee_name,
            splash_image=splash_image,
        )

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5050, debug=True)

