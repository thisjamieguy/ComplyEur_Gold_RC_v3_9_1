"""Minimal Trips API endpoints for testing.

This provides a simplified CRUD API for trips that works alongside
the existing calendar API and main routes.
"""

from flask import Blueprint, request, jsonify, current_app
import sqlite3
from datetime import date
from .util_auth import login_required
from .models import get_db

trips_bp = Blueprint("trips", __name__)


@trips_bp.route("/trips", methods=["POST"])
@login_required
def create_trip():
    """Create a new trip."""
    data = request.get_json(force=True)
    employee_id = data.get("employee_id")
    country = (data.get("country") or "").strip()
    start = data.get("start_date")
    end = data.get("end_date")
    
    if not all([employee_id, country, start, end]):
        return jsonify({"error": "missing fields"}), 400
    
    conn = get_db()
    cur = conn.cursor()
    # Use the main app's schema with entry_date/exit_date
    # Map start_date/end_date to entry_date/exit_date to match main schema
    cur.execute("INSERT INTO trips(employee_id, country, entry_date, exit_date, purpose, job_ref, ghosted) VALUES (?,?,?,?,?,?,?)",
                (employee_id, country, start, end, data.get("purpose"), data.get("job_ref"), data.get("ghosted", False)))
    tid = cur.lastrowid
    conn.commit()
    # Force WAL checkpoint to ensure changes are visible to other connections
    try:
        cur.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    except Exception:
        pass  # Best effort - checkpoint might not be needed
    # Connection managed by Flask teardown handler
    return jsonify({"id": tid}), 201


@trips_bp.route("/trips", methods=["GET"])
@login_required
def list_trips():
    """List all trips."""
    conn = get_db()
    cur = conn.cursor()
    # Map entry_date/exit_date back to start_date/end_date for API compatibility
    cur.execute("SELECT id, employee_id, country, entry_date, exit_date FROM trips ORDER BY entry_date ASC")
    rows = [{"id": r[0], "employee_id": r[1], "country": r[2], "start_date": r[3], "end_date": r[4]} for r in cur.fetchall()]
    # Connection managed by Flask teardown handler
    return jsonify(rows), 200


@trips_bp.route("/trips/<int:trip_id>", methods=["PATCH"])
@login_required
def update_trip(trip_id):
    """Update an existing trip."""
    data = request.get_json(force=True)
    conn = get_db()
    cur = conn.cursor()
    
    updates = []
    values = []
    
    if "start_date" in data:
        updates.append("entry_date = ?")
        values.append(data["start_date"])
    if "end_date" in data:
        updates.append("exit_date = ?")
        values.append(data["end_date"])
    if "country" in data:
        updates.append("country = ?")
        values.append(data["country"])
    if "employee_id" in data:
        updates.append("employee_id = ?")
        values.append(data["employee_id"])
    
    if not updates:
        return jsonify({"error": "No fields to update"}), 400
    
    values.append(trip_id)
    cur.execute(f"UPDATE trips SET {', '.join(updates)} WHERE id = ?", values)
    conn.commit()
    
    if cur.rowcount == 0:
        return jsonify({"error": "Trip not found"}), 404
    
    # Return updated trip
    cur.execute("SELECT id, employee_id, country, entry_date, exit_date FROM trips WHERE id = ?", (trip_id,))
    row = cur.fetchone()
    
    if not row:
        return jsonify({"error": "Trip not found"}), 404
    
    return jsonify({
        "id": row[0],
        "employee_id": row[1],
        "country": row[2],
        "start_date": row[3],
        "end_date": row[4]
    }), 200


@trips_bp.route("/trips/<int:trip_id>", methods=["DELETE"])
@login_required
def delete_trip(trip_id):
    """Delete a trip."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM trips WHERE id = ?", (trip_id,))
    conn.commit()
    deleted = cur.rowcount > 0
    # Connection managed by Flask teardown handler
    
    if not deleted:
        return jsonify({"error": "Trip not found"}), 404
    
    return jsonify({"success": True}), 200
