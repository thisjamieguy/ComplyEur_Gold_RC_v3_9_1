"""SQLite helpers for DSAR operations."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from typing import Any, Dict, List, Optional


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_employee(db_path: str, employee_id: int) -> Optional[Dict[str, Any]]:
    with closing(_connect(db_path)) as conn:
        cursor = conn.execute("SELECT id, name FROM employees WHERE id = ?", (employee_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def fetch_employee_name(db_path: str, employee_id: int) -> Optional[str]:
    with closing(_connect(db_path)) as conn:
        cursor = conn.execute("SELECT name FROM employees WHERE id = ?", (employee_id,))
        row = cursor.fetchone()
        return row["name"] if row else None


def fetch_employee_trips(db_path: str, employee_id: int) -> List[Dict[str, Any]]:
    query = """
        SELECT id, country, entry_date, exit_date, travel_days, created_at, is_private, purpose
        FROM trips
        WHERE employee_id = ?
        ORDER BY entry_date ASC
    """
    with closing(_connect(db_path)) as conn:
        cursor = conn.execute(query, (employee_id,))
        return [dict(row) for row in cursor.fetchall()]


def count_employee_trips(db_path: str, employee_id: int) -> int:
    with closing(_connect(db_path)) as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM trips WHERE employee_id = ?", (employee_id,))
        result = cursor.fetchone()
        return int(result[0]) if result else 0


def delete_employee_and_trips(db_path: str, employee_id: int) -> Optional[Dict[str, Any]]:
    with closing(_connect(db_path)) as conn:
        cursor = conn.execute("SELECT name FROM employees WHERE id = ?", (employee_id,))
        row = cursor.fetchone()
        if not row:
            return None
        employee_name = row["name"]
        trip_cursor = conn.execute("SELECT COUNT(*) FROM trips WHERE employee_id = ?", (employee_id,))
        trips_count = int(trip_cursor.fetchone()[0])
        conn.execute("DELETE FROM trips WHERE employee_id = ?", (employee_id,))
        conn.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
        conn.commit()
        return {"name": employee_name, "trips_deleted": trips_count}


def update_employee_name(db_path: str, employee_id: int, new_name: str) -> bool:
    with closing(_connect(db_path)) as conn:
        cursor = conn.execute("UPDATE employees SET name = ? WHERE id = ?", (new_name, employee_id))
        conn.commit()
        return cursor.rowcount > 0
