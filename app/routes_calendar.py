"""Calendar API blueprint providing trip CRUD endpoints for the React calendar."""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from flask import Blueprint, jsonify, request

from .models import Trip, get_db


logger = logging.getLogger(__name__)

bp = Blueprint("calendar_api", __name__, url_prefix="/api")


MAX_FUTURE_YEARS = 10
MIN_ALLOWED_YEAR = 1990


def _validate_year_range(candidate: date, field_name: str) -> None:
    current_year = datetime.utcnow().year
    if candidate.year < MIN_ALLOWED_YEAR or candidate.year > current_year + MAX_FUTURE_YEARS:
        raise ValueError(
            f"{field_name} year must be between {MIN_ALLOWED_YEAR} and {current_year + MAX_FUTURE_YEARS}"
        )


def _normalize_to_date(value: Any, field_name: str) -> date:
    if isinstance(value, datetime):
        result = value.date()
        _validate_year_range(result, field_name)
        return result
    if isinstance(value, date):
        _validate_year_range(value, field_name)
        return value
    if isinstance(value, str):
        value = value.strip()
        if not value:
            raise ValueError(f"{field_name} cannot be blank")
        try:
            candidate = datetime.fromisoformat(value.replace("Z", "")).date()
            _validate_year_range(candidate, field_name)
            return candidate
        except ValueError:
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
                try:
                    candidate = datetime.strptime(value, fmt).date()
                    _validate_year_range(candidate, field_name)
                    return candidate
                except ValueError:
                    continue
        raise ValueError(f"{field_name} must be an ISO date string")
    raise ValueError(f"Unsupported value for {field_name}")


def _ensure_iso_date(value: Any, field_name: str) -> str:
    """Normalise an incoming date value to YYYY-MM-DD."""
    if value is None:
        raise ValueError(f"{field_name} is required")
    normalized = _normalize_to_date(value, field_name)
    return normalized.isoformat()


def _close_conn(conn) -> None:
    """Close SQLite connection unless it's the shared in-memory reference."""
    try:
        from flask import current_app

        db_path = current_app.config.get("DATABASE", "")
        if isinstance(db_path, str) and db_path.startswith("file:eu_memdb"):
            return
        conn.close()
    except Exception:  # pragma: no cover - best-effort cleanup
        pass


def _trip_from_row(row: Dict[str, Any]) -> Dict[str, Any]:
    row_data = dict(row)
    employee_name = row_data.pop("employee_name", None)
    trip = Trip(**row_data)
    payload = trip.to_dict(employee_name=employee_name)
    # Enrich with convenience metadata for the UI
    payload.setdefault("employee", employee_name)
    payload.setdefault("job_ref", payload.get("job_ref") or "")
    payload["duration_days"] = _calculate_duration(payload["start_date"], payload["end_date"])
    return payload


def _calculate_duration(start_iso: Optional[str], end_iso: Optional[str]) -> Optional[int]:
    if not start_iso or not end_iso:
        return None
    try:
        start_dt = datetime.fromisoformat(start_iso).date()
        end_dt = datetime.fromisoformat(end_iso).date()
        return (end_dt - start_dt).days + 1
    except ValueError:
        return None


def _get_trip_payload(trip_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT t.*, e.name AS employee_name
        FROM trips t
        LEFT JOIN employees e ON e.id = t.employee_id
        WHERE t.id = ?
        """,
        (trip_id,),
    )
    row = cursor.fetchone()
    if row is None:
        _close_conn(conn)
        return None
    payload = _trip_from_row(row)
    _close_conn(conn)
    return payload


def _validate_employee(cursor, employee_id: int) -> bool:
    cursor.execute("SELECT 1 FROM employees WHERE id = ?", (employee_id,))
    return cursor.fetchone() is not None


@bp.route("/employees", methods=["GET"])
def list_employees():
    """Return all employees for calendar row rendering."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, name, 1 AS active FROM employees ORDER BY name COLLATE NOCASE"
    )
    employees = [
        {
            "id": int(row["id"]),
            "name": row["name"],
            "active": bool(row["active"]),
        }
        for row in cursor.fetchall()
    ]

    _close_conn(conn)
    # Maintain backward compatibility with earlier payload shape while exposing the
    # flat list the new React hooks expect.
    response = jsonify(employees)
    response.headers.setdefault("X-Payload-Variant", "list")
    return response


@bp.route("/trips", methods=["GET"])
def get_trips():
    """Return trips (optionally filtered by date range) and employees."""
    start = request.args.get("start") or request.args.get("start_date")
    end = request.args.get("end") or request.args.get("end_date")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, name FROM employees ORDER BY name COLLATE NOCASE")
    employees = [dict(row) for row in cursor.fetchall()]

    query = [
        "SELECT t.*, e.name AS employee_name",
        "FROM trips t",
        "LEFT JOIN employees e ON e.id = t.employee_id",
    ]
    params: List[Any] = []
    if start and end:
        try:
            start_iso = _ensure_iso_date(start, "start")
            end_iso = _ensure_iso_date(end, "end")
        except ValueError as exc:
            _close_conn(conn)
            return jsonify({"error": str(exc)}), 400
        query.append("WHERE t.entry_date <= ? AND t.exit_date >= ?")
        params.extend([end_iso, start_iso])
    elif start:
        try:
            end_iso = _ensure_iso_date(start, "start")
        except ValueError as exc:
            _close_conn(conn)
            return jsonify({"error": str(exc)}), 400
        query.append("WHERE t.exit_date >= ?")
        params.append(end_iso)
    elif end:
        try:
            end_iso = _ensure_iso_date(end, "end")
        except ValueError as exc:
            _close_conn(conn)
            return jsonify({"error": str(exc)}), 400
        query.append("WHERE t.entry_date <= ?")
        params.append(end_iso)

    query.append("ORDER BY e.name COLLATE NOCASE, t.entry_date ASC, t.id ASC")
    cursor.execute("\n".join(query), params)
    trips = [_trip_from_row(row) for row in cursor.fetchall()]

    response = {
        "employees": employees,
        "trips": trips,
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }

    _close_conn(conn)
    return jsonify(response)


@bp.route("/trips/<int:trip_id>", methods=["GET"])
def get_trip(trip_id: int):
    payload = _get_trip_payload(trip_id)
    if payload is None:
        return jsonify({"error": "Trip not found"}), 404
    return jsonify(payload)


def _prepare_trip_updates(
    cursor, data: Dict[str, Any], *, current: Dict[str, Any]
) -> Tuple[Dict[str, Any], Optional[str]]:
    updates: Dict[str, Any] = {}

    if "employee_id" in data:
        try:
            employee_id = int(data["employee_id"])
        except (TypeError, ValueError):
            return updates, "employee_id must be an integer"
        if not _validate_employee(cursor, employee_id):
            return updates, "Employee not found"
        updates["employee_id"] = employee_id

    if "country" in data and data["country"] is not None:
        updates["country"] = str(data["country"]).strip() or current.get("country")

    if "job_ref" in data:
        raw = data.get("job_ref")
        updates["job_ref"] = str(raw).strip() if raw else None

    if "ghosted" in data:
        updates["ghosted"] = 1 if bool(data["ghosted"]) else 0

    if "purpose" in data:
        updates["purpose"] = str(data["purpose"]).strip() if data["purpose"] else None

    date_changes = {}
    if "start_date" in data:
        try:
            date_changes["entry_date"] = _ensure_iso_date(data["start_date"], "start_date")
        except ValueError as exc:
            return updates, str(exc)
    if "end_date" in data:
        try:
            date_changes["exit_date"] = _ensure_iso_date(data["end_date"], "end_date")
        except ValueError as exc:
            return updates, str(exc)

    entry = date_changes.get("entry_date", current.get("entry_date"))
    exit_ = date_changes.get("exit_date", current.get("exit_date"))
    if entry and exit_ and entry > exit_:
        return updates, "start_date must be on or before end_date"

    updates.update(date_changes)
    return updates, None


@bp.route("/trips/<int:trip_id>", methods=["PATCH"])
def update_trip(trip_id: int):
    """Lightweight trip update endpoint with optimistic client support."""
    data = request.get_json(silent=True) or {}

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM trips WHERE id = ?", (trip_id,))
    row = cursor.fetchone()
    if row is None:
        _close_conn(conn)
        return jsonify({"error": "Trip not found"}), 404

    current = dict(row)

    entry_date = None
    exit_date = None
    updates = []
    params = []

    if "start_date" in data:
        try:
            entry_date = _ensure_iso_date(data["start_date"], "start_date")
        except ValueError as exc:
            _close_conn(conn)
            return jsonify({"error": str(exc)}), 400
        updates.append("entry_date = ?")
        params.append(entry_date)

    if "end_date" in data:
        try:
            exit_date = _ensure_iso_date(data["end_date"], "end_date")
        except ValueError as exc:
            _close_conn(conn)
            return jsonify({"error": str(exc)}), 400
        updates.append("exit_date = ?")
        params.append(exit_date)

    if entry_date is None:
        entry_date = current.get("entry_date")
    if exit_date is None:
        exit_date = current.get("exit_date")

    if entry_date and exit_date and entry_date > exit_date:
        _close_conn(conn)
        return jsonify({"error": "start_date must be on or before end_date"}), 400

    if "employee_id" in data:
        try:
            employee_id = int(data["employee_id"])
        except (TypeError, ValueError):
            _close_conn(conn)
            return jsonify({"error": "employee_id must be an integer"}), 400
        if not _validate_employee(cursor, employee_id):
            _close_conn(conn)
            return jsonify({"error": "Employee not found"}), 400
        updates.append("employee_id = ?")
        params.append(employee_id)

    if "ghosted" in data:
        updates.append("ghosted = ?")
        params.append(1 if bool(data["ghosted"]) else 0)

    if "job_ref" in data:
        raw_job_ref = data.get("job_ref")
        updates.append("job_ref = ?")
        params.append(str(raw_job_ref).strip() or None)

    if "country" in data:
        raw_country = data.get("country")
        cleaned_country = str(raw_country).strip() if raw_country is not None else ""
        if not cleaned_country:
            _close_conn(conn)
            return jsonify({"error": "country cannot be blank"}), 400
        updates.append("country = ?")
        params.append(cleaned_country)

    if "purpose" in data:
        raw_purpose = data.get("purpose")
        cleaned_purpose = str(raw_purpose).strip() if raw_purpose is not None else ""
        updates.append("purpose = ?")
        params.append(cleaned_purpose or None)

    if not updates:
        _close_conn(conn)
        payload = _get_trip_payload(trip_id)
        if payload is None:
            return jsonify({"error": "Trip not found"}), 404
        payload["success"] = True
        return jsonify(payload)

    try:
        params.append(trip_id)
        cursor.execute(
            f"UPDATE trips SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        if cursor.rowcount == 0:
            conn.rollback()
            return jsonify({"error": "Trip not found"}), 404
        conn.commit()
    except Exception as exc:  # pragma: no cover - defensive
        conn.rollback()
        logger.exception("Trip update error: %s", exc)
        return jsonify({"error": str(exc)}), 500

    payload = _get_trip_payload(trip_id)
    if payload is None:
        return jsonify({"error": "Trip not found"}), 500
    payload["success"] = True
    return jsonify(payload), 200


@bp.route("/trips", methods=["POST"])
def create_trip():
    data = request.get_json(silent=True) or {}
    return _create_trip(data)


@bp.route("/trips/<int:trip_id>", methods=["DELETE"])
def delete_trip(trip_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM trips WHERE id = ?", (trip_id,))
    if cursor.fetchone() is None:
        _close_conn(conn)
        return jsonify({"error": "Trip not found"}), 404

    cursor.execute("DELETE FROM trips WHERE id = ?", (trip_id,))
    conn.commit()
    _close_conn(conn)
    return jsonify({"success": True})


@bp.route("/trips/<int:trip_id>/duplicate", methods=["POST"])
def duplicate_trip(trip_id: int):
    """Clone an existing trip. Optional overrides may be supplied in the body."""
    source = _get_trip_payload(trip_id)
    if source is None:
        return jsonify({"error": "Trip not found"}), 404

    overrides = request.get_json(silent=True) or {}
    payload = {**source, **overrides}
    payload["employee_id"] = payload.get("employee_id") or source.get("employee_id")

    # Remove identifiers to allow create handler to insert a new record
    payload.pop("id", None)
    return _create_trip(payload)


def _create_trip(payload: Dict[str, Any]):
    """Shared create logic used by POST /trips and duplicate."""
    required = {"employee_id", "country", "start_date", "end_date"}
    missing = [field for field in required if not payload.get(field)]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    conn = get_db()
    cursor = conn.cursor()

    try:
        employee_id = int(payload["employee_id"])
    except (TypeError, ValueError):
        _close_conn(conn)
        return jsonify({"error": "employee_id must be an integer"}), 400

    if not _validate_employee(cursor, employee_id):
        _close_conn(conn)
        return jsonify({"error": "Employee not found"}), 400

    try:
        entry_date = _ensure_iso_date(payload["start_date"], "start_date")
        exit_date = _ensure_iso_date(payload["end_date"], "end_date")
    except ValueError as exc:
        _close_conn(conn)
        return jsonify({"error": str(exc)}), 400

    if entry_date > exit_date:
        _close_conn(conn)
        return jsonify({"error": "start_date must be on or before end_date"}), 400

    ghosted = 1 if bool(payload.get("ghosted")) else 0

    cursor.execute(
        """
        INSERT INTO trips (employee_id, country, entry_date, exit_date, job_ref, ghosted, purpose)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            employee_id,
            str(payload["country"]).strip(),
            entry_date,
            exit_date,
            str(payload.get("job_ref", "")).strip() or None,
            ghosted,
            str(payload.get("purpose", "")).strip() or None,
        ),
    )
    conn.commit()
    new_id = cursor.lastrowid
    _close_conn(conn)

    created = _get_trip_payload(new_id)
    if created is None:
        return jsonify({"error": "Failed to load persisted trip"}), 500
    return jsonify(created), 201
