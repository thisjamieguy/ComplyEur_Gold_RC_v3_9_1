import os
import sqlite3
import pytest

from app import create_app
from app.models import get_db


@pytest.fixture
def app_with_isolated_db(tmp_path, monkeypatch):
    """Provide an app bound to a temporary SQLite database."""
    db_path = tmp_path / "crud_test.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_path))
    app = create_app()
    yield app


def test_employee_trip_crud_cycle(app_with_isolated_db):
    """Round-trip verify create, read, update, delete operations."""
    with app_with_isolated_db.app_context():
        conn = get_db()
        cur = conn.cursor()

        # Create employee and trip
        cur.execute("INSERT INTO employees (name) VALUES (?)", ("Test Employee",))
        employee_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO trips (employee_id, country, entry_date, exit_date, travel_days)
            VALUES (?, ?, ?, ?, ?)
            """,
            (employee_id, "FR", "2024-01-01", "2024-01-05", 5),
        )
        trip_id = cur.lastrowid
        conn.commit()

        # Read back
        cur.execute("SELECT name FROM employees WHERE id = ?", (employee_id,))
        assert cur.fetchone()["name"] == "Test Employee"

        # Update
        cur.execute(
            "UPDATE trips SET exit_date = ?, travel_days = ? WHERE id = ?",
            ("2024-01-04", 4, trip_id),
        )
        conn.commit()
        cur.execute("SELECT exit_date, travel_days FROM trips WHERE id = ?", (trip_id,))
        row = cur.fetchone()
        assert row["exit_date"] == "2024-01-04"
        assert row["travel_days"] == 4

        # Delete
        cur.execute("DELETE FROM trips WHERE id = ?", (trip_id,))
        cur.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
        conn.commit()

        cur.execute("SELECT COUNT(*) FROM trips WHERE id = ?", (trip_id,))
        assert cur.fetchone()[0] == 0
        cur.execute("SELECT COUNT(*) FROM employees WHERE id = ?", (employee_id,))
        assert cur.fetchone()[0] == 0
