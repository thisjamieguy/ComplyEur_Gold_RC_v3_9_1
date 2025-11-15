"""Database helpers for the what-if scenario domain."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from typing import Any, Dict, List, Optional


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_employees(db_path: str) -> List[Dict[str, Any]]:
    with closing(_connect(db_path)) as conn:
        cursor = conn.execute("SELECT id, name FROM employees ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]


def fetch_employee_trips(db_path: str, employee_id: int) -> List[Dict[str, Any]]:
    with closing(_connect(db_path)) as conn:
        cursor = conn.execute(
            "SELECT entry_date, exit_date, country FROM trips WHERE employee_id = ?",
            (employee_id,),
        )
        return [
            {
                "entry_date": row["entry_date"],
                "exit_date": row["exit_date"],
                "country": row["country"],
            }
            for row in cursor.fetchall()
        ]


def fetch_employee_name(db_path: str, employee_id: int) -> Optional[str]:
    with closing(_connect(db_path)) as conn:
        cursor = conn.execute("SELECT name FROM employees WHERE id = ?", (employee_id,))
        row = cursor.fetchone()
        return row["name"] if row else None
