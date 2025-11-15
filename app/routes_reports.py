"""Reports and export endpoints."""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    current_app,
    jsonify,
    make_response,
    render_template,
    request,
)

from app.services import reports_service
from app.services.exports import export_trips_csv
from app.services.rolling90 import COMPLIANCE_START_DATE

from .util_auth import login_required


logger = logging.getLogger(__name__)
reports_bp = Blueprint("reports", __name__)


def _config():
    return current_app.config["CONFIG"]


def _db_path() -> str:
    return current_app.config["DATABASE"]


@reports_bp.route("/future_job_alerts")
@login_required
def future_job_alerts():
    """Render the future job alerts dashboard."""
    config = _config()
    warning_threshold = config.get("FUTURE_JOB_WARNING_THRESHOLD", 80)
    compliance_start_date = COMPLIANCE_START_DATE

    risk_filter = request.args.get("risk", "all")
    sort_by = request.args.get("sort", "risk")

    forecasts = reports_service.get_future_alerts(
        _db_path(),
        warning_threshold,
        compliance_start_date,
    )
    summary = reports_service.summarise_future_alerts(forecasts)
    filtered = reports_service.filter_and_sort_future_alerts(
        forecasts,
        risk_filter=risk_filter,
        sort_by=sort_by,
    )

    return render_template(
        "future_job_alerts.html",
        forecasts=filtered,
        red_count=summary["red"],
        yellow_count=summary["yellow"],
        green_count=summary["green"],
        warning_threshold=warning_threshold,
        risk_filter=risk_filter,
        sort_by=sort_by,
    )


@reports_bp.route("/export_future_alerts")
@login_required
def export_future_alerts():
    """Return the future job alerts CSV."""
    config = _config()
    warning_threshold = config.get("FUTURE_JOB_WARNING_THRESHOLD", 80)
    csv_data = reports_service.generate_future_alerts_csv(
        _db_path(),
        warning_threshold,
        COMPLIANCE_START_DATE,
    )
    response = make_response(csv_data)
    response.headers["Content-Type"] = "text/csv"
    response.headers["Content-Disposition"] = (
        "attachment; filename=future_job_alerts.csv"
    )
    return response


@reports_bp.route("/export/trips/csv")
@login_required
def export_trips_csv_route():
    """Export trips for all employees as CSV."""
    try:
        csv_data = export_trips_csv(_db_path())
    except Exception as exc:  # pragma: no cover - legacy CSV exporter
        logger.error("Error exporting trips CSV: %s", exc)
        return jsonify({"success": False, "error": str(exc)}), 500

    response = make_response(csv_data)
    response.headers["Content-Type"] = "text/csv"
    response.headers["Content-Disposition"] = "attachment; filename=trips.csv"
    return response

