"""Minimal Employees API endpoints for testing.

This provides a simplified CRUD API for employees that works alongside
the existing calendar API and main routes.
"""

from flask import Blueprint, request, jsonify, current_app
import sqlite3
from .util_auth import login_required

employees_bp = Blueprint("employees", __name__)


def _db():
    """Get database connection."""
    db_path = current_app.config.get("DATABASE") or current_app.config.get("DB_PATH", "data/complyeur.db")
    return sqlite3.connect(db_path)


@employees_bp.route("/employees", methods=["GET"])
@login_required
def list_employees():
    """List all employees."""
    con = _db()
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS employees (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
    cur.execute("SELECT id, name FROM employees ORDER BY name ASC")
    rows = [{"id": r[0], "name": r[1]} for r in cur.fetchall()]
    con.close()
    return jsonify(rows), 200


@employees_bp.route("/employees", methods=["POST"])
@login_required
def create_employee():
    """Create a new employee."""
    data = request.get_json(force=True)
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name required"}), 400
    
    con = _db()
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS employees (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
    cur.execute("INSERT INTO employees(name) VALUES (?)", (name,))
    con.commit()
    eid = cur.lastrowid
    con.close()
    return jsonify({"id": eid, "name": name}), 201
