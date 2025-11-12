from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable

import pytest

from app.models import get_db
from app.services.alerts import check_alert_status
from app.services.rolling90 import days_used_in_window, presence_days


@pytest.fixture
def fixed_today(monkeypatch):
    target = date(2024, 6, 30)

    class _FixedDate(date):
        @classmethod
        def today(cls):  # type: ignore[override]
            return target

    monkeypatch.setattr("app.services.alerts.date", _FixedDate)
    monkeypatch.setattr("app.routes_calendar.date", _FixedDate)
    monkeypatch.setattr("app.routes_calendar.timedelta", timedelta)
    return target


def _iter_trips(conn) -> Iterable[dict]:
    cursor = conn.execute(
        """
        SELECT id, employee_id, entry_date, exit_date, travel_days
        FROM trips
        ORDER BY employee_id, entry_date
        """
    )
    for row in cursor.fetchall():
        yield dict(row)


def test_trip_travel_days_are_consistent(phase38_app):
    with phase38_app.app_context():
        conn = get_db()
        mismatches = []
        for row in _iter_trips(conn):
            start = date.fromisoformat(row["entry_date"])
            end = date.fromisoformat(row["exit_date"])
            expected = (end - start).days + 1
            if expected != row["travel_days"]:
                mismatches.append((row["id"], expected, row["travel_days"]))
        assert not mismatches, f"Unexpected travel day mismatch: {mismatches}"


def test_forecast_matches_database(phase38_client, phase38_app, fixed_today):
    employee_ids = (1, 2, 3)
    with phase38_app.app_context():
        conn = get_db()
        for employee_id in employee_ids:
            cursor = conn.execute(
                "SELECT entry_date, exit_date, country FROM trips WHERE employee_id = ?",
                (employee_id,),
            )
            trips = [dict(row) for row in cursor.fetchall()]
            presence = presence_days(trips)
            expected_used = days_used_in_window(presence, fixed_today)

            response = phase38_client.get(f"/api/forecast/{employee_id}")
            assert response.status_code == 200
            payload = response.get_json()
            assert payload["used_days"] == expected_used
            assert payload["projected_total"] >= payload["used_days"]


def test_alert_refresh_synchronizes_with_db(phase38_app, fixed_today):
    expected_risks = {1: None, 2: "RED", 3: "RED"}
    with phase38_app.app_context():
        results = {}
        for employee_id, expected in expected_risks.items():
            risk = check_alert_status(employee_id)
            results[employee_id] = risk
            if expected is None:
                assert risk is None
            else:
                assert risk == expected

        conn = get_db()
        cursor = conn.execute(
            "SELECT employee_id, risk_level, resolved FROM alerts WHERE resolved = 0"
        )
        active = {row["employee_id"]: row["risk_level"] for row in cursor.fetchall()}
        for employee_id, risk in expected_risks.items():
            if risk is None:
                assert employee_id not in active
            else:
                assert active.get(employee_id) == risk
