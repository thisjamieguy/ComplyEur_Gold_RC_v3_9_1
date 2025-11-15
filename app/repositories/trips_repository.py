"""Trip persistence helpers."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from app.models import get_db

SELECT_BASE = "SELECT id, employee_id, country, entry_date, exit_date FROM trips"


def _row_to_trip(row) -> dict[str, Any]:
    if row is None:
        return {}
    return {
        "id": row["id"],
        "employee_id": row["employee_id"],
        "country": row["country"],
        "start_date": row["entry_date"],
        "end_date": row["exit_date"],
    }


def insert_trip(payload: Mapping[str, Any]) -> int:
    """Insert a trip and return its id."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO trips(employee_id, country, entry_date, exit_date, purpose, job_ref, ghosted)
        VALUES (?,?,?,?,?,?,?)
        """,
        (
            payload["employee_id"],
            payload["country"],
            payload["start_date"],
            payload["end_date"],
            payload.get("purpose"),
            payload.get("job_ref"),
            payload.get("ghosted", False),
        ),
    )
    trip_id = cursor.lastrowid
    conn.commit()
    try:
        cursor.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    except Exception:
        pass
    return int(trip_id)


def fetch_all() -> list[dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"{SELECT_BASE} ORDER BY entry_date ASC")
    return [_row_to_trip(row) for row in cursor.fetchall()]


def fetch_by_id(trip_id: int) -> dict[str, Any] | None:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"{SELECT_BASE} WHERE id = ?", (trip_id,))
    row = cursor.fetchone()
    return _row_to_trip(row) if row else None


def update_trip(trip_id: int, updates: Mapping[str, Any]) -> int:
    """Return affected row count."""
    if not updates:
        return 0
    conn = get_db()
    cursor = conn.cursor()
    assignments = ", ".join(f"{column} = ?" for column in updates.keys())
    params: Sequence[Any] = list(updates.values()) + [trip_id]  # type: ignore[arg-type]
    cursor.execute(f"UPDATE trips SET {assignments} WHERE id = ?", params)
    conn.commit()
    return cursor.rowcount


def delete_trip(trip_id: int) -> bool:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM trips WHERE id = ?", (trip_id,))
    conn.commit()
    return cursor.rowcount > 0
