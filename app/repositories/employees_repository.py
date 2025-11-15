"""SQLite access helpers for the Employees domain."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from typing import Any, Mapping

EMPLOYEE_TABLE_SQL = "CREATE TABLE IF NOT EXISTS employees (id INTEGER PRIMARY KEY, name TEXT NOT NULL)"


def _resolve_db_path(config: Mapping[str, Any]) -> str:
    """Mirror the legacy resolution logic for DATABASE / DB_PATH."""
    return config.get("DATABASE") or config.get("DB_PATH", "data/complyeur.db")


def _connect(db_path: str) -> sqlite3.Connection:
    """Open a SQLite connection for direct repository access."""
    return sqlite3.connect(db_path)


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(EMPLOYEE_TABLE_SQL)


def fetch_all(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return all employees ordered by name (legacy behaviour)."""
    db_path = _resolve_db_path(config)
    with closing(_connect(db_path)) as conn:
        _ensure_schema(conn)
        cursor = conn.execute("SELECT id, name FROM employees ORDER BY name ASC")
        return [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]


def insert_employee(config: Mapping[str, Any], name: str) -> int:
    """Insert a new employee and return its id."""
    db_path = _resolve_db_path(config)
    with closing(_connect(db_path)) as conn:
        _ensure_schema(conn)
        cursor = conn.execute("INSERT INTO employees(name) VALUES (?)", (name,))
        conn.commit()
        return int(cursor.lastrowid)
