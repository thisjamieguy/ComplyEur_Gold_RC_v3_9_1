"""Privacy & GDPR domain endpoints (retention + DSAR tooling)."""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    current_app,
    jsonify,
    render_template,
    request,
    send_file,
)

from app.services.audit import write_audit
from app.services.dsar import (
    create_dsar_export,
    delete_employee_data,
    rectify_employee_name,
)
from app.services.retention import (
    anonymize_employee,
    get_expired_trips,
    purge_expired_trips,
)

from .util_auth import login_required


logger = logging.getLogger(__name__)
privacy_bp = Blueprint("privacy", __name__)


def _config():
    return current_app.config["CONFIG"]


def _db_path():
    return current_app.config["DATABASE"]


@privacy_bp.route("/api/retention/preview")
@login_required
def retention_preview():
    """Return counts for expired trips that qualify for retention purging."""
    config = _config()
    retention_months = config.get("RETENTION_MONTHS", 36)
    db_path = _db_path()
    try:
        trips = get_expired_trips(db_path, retention_months)
        employees_affected = len({t["employee_id"] for t in trips})
        return jsonify(
            {
                "success": True,
                "trips_count": len(trips),
                "employees_affected": employees_affected,
            }
        )
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Retention preview error: %s", exc)
        return jsonify({"success": False, "error": str(exc)}), 500


@privacy_bp.route("/admin/retention/expired")
@login_required
def retention_expired():
    """Render the expired trips list for manual review before purging."""
    config = _config()
    retention_months = config.get("RETENTION_MONTHS", 36)
    db_path = _db_path()
    try:
        trips = get_expired_trips(db_path, retention_months)
    except Exception:
        trips = []
    return render_template(
        "expired_trips.html", trips=trips, retention_months=retention_months
    )


@privacy_bp.route("/admin/retention/purge", methods=["POST"])
@login_required
def retention_purge():
    """Purge expired trips and emit audit trail entries."""
    config = _config()
    db_path = _db_path()
    retention_months = config.get("RETENTION_MONTHS", 36)
    audit_log = config["AUDIT_LOG_PATH"]
    try:
        result = purge_expired_trips(db_path, retention_months)
        write_audit(audit_log, "retention_purge", "admin", result)
        payload = {"success": True}
        payload.update(result)
        return jsonify(payload)
    except Exception as exc:
        logger.error("Retention purge error: %s", exc)
        write_audit(audit_log, "retention_purge_error", "admin", {"error": str(exc)})
        return jsonify({"success": False, "error": str(exc)}), 500


@privacy_bp.route("/admin/dsar/export/<int:employee_id>")
@login_required
def dsar_export(employee_id: int):
    """Generate a DSAR export for a specific employee."""
    config = _config()
    db_path = _db_path()
    try:
        result = create_dsar_export(
            db_path,
            employee_id,
            config["DSAR_EXPORT_DIR"],
            config.get("RETENTION_MONTHS", 36),
        )
    except Exception as exc:
        logger.error("DSAR export error: %s", exc)
        write_audit(
            config["AUDIT_LOG_PATH"],
            "dsar_export_error",
            "admin",
            {"employee_id": employee_id, "error": str(exc)},
        )
        return jsonify({"success": False, "error": str(exc)}), 500

    if not result.get("success"):
        return jsonify(result), 404

    write_audit(
        config["AUDIT_LOG_PATH"],
        "dsar_export",
        "admin",
        {"employee_id": employee_id, "file": result["filename"]},
    )
    return send_file(
        result["file_path"], as_attachment=True, download_name=result["filename"]
    )


@privacy_bp.route("/admin/dsar/rectify/<int:employee_id>", methods=["POST"])
@login_required
def dsar_rectify(employee_id: int):
    """Rectify an employee name as part of the DSAR toolkit."""
    config = _config()
    db_path = _db_path()
    try:
        payload = request.get_json(force=True) or {}
        new_name = (payload.get("new_name") or "").strip()
        result = rectify_employee_name(db_path, employee_id, new_name)
        audit_action = "dsar_rectify" if result.get("success") else "dsar_rectify_failed"
        audit_payload = {"employee_id": employee_id}
        if result.get("success"):
            audit_payload["new_name"] = new_name
        else:
            audit_payload["error"] = result.get("error")
        write_audit(config["AUDIT_LOG_PATH"], audit_action, "admin", audit_payload)
        return jsonify(result)
    except Exception as exc:
        logger.error("DSAR rectify error: %s", exc)
        write_audit(
            config["AUDIT_LOG_PATH"],
            "dsar_rectify_error",
            "admin",
            {"employee_id": employee_id, "error": str(exc)},
        )
        return jsonify({"success": False, "error": str(exc)}), 500


@privacy_bp.route("/admin/dsar/delete/<int:employee_id>", methods=["POST"])
@login_required
def dsar_delete(employee_id: int):
    """Delete all data for an employee."""
    config = _config()
    db_path = _db_path()
    try:
        result = delete_employee_data(db_path, employee_id)
        audit_action = "dsar_delete" if result.get("success") else "dsar_delete_failed"
        audit_payload = {"employee_id": employee_id}
        if result.get("success"):
            audit_payload["trips_deleted"] = result.get("trips_deleted", 0)
        else:
            audit_payload["error"] = result.get("error")
        write_audit(config["AUDIT_LOG_PATH"], audit_action, "admin", audit_payload)
        return jsonify(result)
    except Exception as exc:
        logger.error("DSAR delete error: %s", exc)
        write_audit(
            config["AUDIT_LOG_PATH"],
            "dsar_delete_error",
            "admin",
            {"employee_id": employee_id, "error": str(exc)},
        )
        return jsonify({"success": False, "error": str(exc)}), 500


@privacy_bp.route("/admin/dsar/anonymize/<int:employee_id>", methods=["POST"])
@login_required
def dsar_anonymize(employee_id: int):
    """Anonymise an employee record; keeps trip rows but removes PII."""
    config = _config()
    db_path = _db_path()
    try:
        result = anonymize_employee(db_path, employee_id)
        audit_action = (
            "dsar_anonymize" if result.get("success") else "dsar_anonymize_failed"
        )
        audit_payload = {"employee_id": employee_id}
        if result.get("success"):
            audit_payload["new_name"] = result.get("new_name")
        else:
            audit_payload["error"] = result.get("error")
        write_audit(config["AUDIT_LOG_PATH"], audit_action, "admin", audit_payload)
        return jsonify(result)
    except Exception as exc:
        logger.error("DSAR anonymize error: %s", exc)
        write_audit(
            config["AUDIT_LOG_PATH"],
            "dsar_anonymize_error",
            "admin",
            {"employee_id": employee_id, "error": str(exc)},
        )
        return jsonify({"success": False, "error": str(exc)}), 500


@privacy_bp.route("/admin_privacy_tools")
@login_required
def admin_privacy_tools():
    """Render the privacy tools dashboard card."""
    config = _config()
    retention_months = config.get("RETENTION_MONTHS", 36)
    expired_count = 0
    try:
        trips = get_expired_trips(_db_path(), retention_months)
        expired_count = len(trips)
    except Exception:  # pragma: no cover - best-effort status
        expired_count = 0
    return render_template(
        "admin_privacy_tools.html",
        retention_months=retention_months,
        expired_count=expired_count,
        last_purge=None,
    )


@privacy_bp.route("/admin/privacy-tools")
@login_required
def admin_privacy_tools_alias():
    """Alias endpoint retained for backwards compatibility."""
    return admin_privacy_tools()

