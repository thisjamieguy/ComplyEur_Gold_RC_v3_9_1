"""Data access helpers for reporting/export workloads."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from typing import Any, Dict, Iterable, List, Optional


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_trips_for_csv(db_path: str, employee_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Return trip rows with employee names for CSV generation."""
    base_query = """
        SELECT employees.name, trips.country, trips.entry_date,
               trips.exit_date,
               CAST(julianday(trips.exit_date) - julianday(trips.entry_date) + 1 AS INTEGER) AS travel_days
        FROM trips
        JOIN employees ON trips.employee_id = employees.id
    """
    order_clause = " ORDER BY employees.name, trips.entry_date DESC"
    params: Iterable[Any] = ()
    if employee_id:
        base_query += " WHERE trips.employee_id = ?"
        order_clause = " ORDER BY trips.entry_date DESC"
        params = (employee_id,)

    with closing(_connect(db_path)) as conn:
        cursor = conn.execute(base_query + order_clause, params)
        return [dict(row) for row in cursor.fetchall()]


def fetch_employee(db_path: str, employee_id: int) -> Optional[Dict[str, Any]]:
    """Return an employee row or None."""
    with closing(_connect(db_path)) as conn:
        cursor = conn.execute("SELECT id, name FROM employees WHERE id = ?", (employee_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def fetch_employee_trips(db_path: str, employee_id: int) -> List[Dict[str, Any]]:
    """Return trips for a specific employee."""
    with closing(_connect(db_path)) as conn:
        cursor = conn.execute(
            "SELECT country, entry_date, exit_date, travel_days FROM trips WHERE employee_id = ? ORDER BY entry_date DESC",
            (employee_id,),
        )
        return [dict(row) for row in cursor.fetchall()]


def fetch_employees_with_trips(db_path: str) -> List[Dict[str, Any]]:
    """Return employees along with their trips (entry/exit/country).

    OPTIMIZED: Single JOIN query instead of N+1 queries.
    """
    with closing(_connect(db_path)) as conn:
        # Single query with LEFT JOIN to fetch all employees and their trips
        # LEFT JOIN ensures employees without trips are still included
        cursor = conn.execute("""
            SELECT
                e.id,
                e.name,
                t.entry_date,
                t.exit_date,
                t.country
            FROM employees e
            LEFT JOIN trips t ON e.id = t.employee_id
            ORDER BY e.name, t.entry_date DESC
        """)

        # Group trips by employee
        results: List[Dict[str, Any]] = []
        current_employee_id: Optional[int] = None
        current_employee: Optional[Dict[str, Any]] = None

        for row in cursor.fetchall():
            emp_id = row["id"]

            # New employee encountered
            if emp_id != current_employee_id:
                # Save previous employee if exists
                if current_employee is not None:
                    results.append(current_employee)

                # Start new employee
                current_employee_id = emp_id
                current_employee = {
                    "id": emp_id,
                    "name": row["name"],
                    "trips": []
                }

            # Add trip if exists (LEFT JOIN may return NULL for employees without trips)
            if row["entry_date"] is not None:
                current_employee["trips"].append({
                    "entry_date": row["entry_date"],
                    "exit_date": row["exit_date"],
                    "country": row["country"],
                })

        # Don't forget the last employee
        if current_employee is not None:
            results.append(current_employee)

        return results
