from __future__ import annotations

from datetime import date

import pytest

from app.models import get_db
from app.services.alerts import check_alert_status


@pytest.mark.usefixtures("phase38_app")
class TestTripUpdateApi:
    def test_drag_updates_trip_dates_and_persists(self, phase38_app, phase38_client):
        trip_id = 2
        new_start = "2024-06-12"
        new_end = "2024-06-25"

        response = phase38_client.post(
            "/api/update_trip_dates",
            json={"trip_id": trip_id, "start_date": new_start, "end_date": new_end},
        )
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["start_date"] == new_start
        assert payload["end_date"] == new_end
        assert payload["duration_days"] == 14  # inclusive day count

        with phase38_app.app_context():
            conn = get_db()
            row = conn.execute(
                "SELECT entry_date, exit_date FROM trips WHERE id = ?", (trip_id,)
            ).fetchone()
            assert row["entry_date"] == new_start
            assert row["exit_date"] == new_end

    def test_resize_validates_chronology(self, phase38_client):
        response = phase38_client.post(
            "/api/update_trip_dates",
            json={
                "trip_id": 3,
                "start_date": "2024-07-10",
                "end_date": "2024-07-01",
            },
        )
        assert response.status_code == 400
        payload = response.get_json()
        assert "start_date must be on or before end_date" in payload["error"]

    def test_patch_trip_updates_alert_state(self, phase38_app, phase38_client, monkeypatch):
        trip_id = 4
        with phase38_app.app_context():
            conn = get_db()
            original_row = conn.execute(
                "SELECT entry_date, exit_date FROM trips WHERE id = ?",
                (trip_id,),
            ).fetchone()
        assert original_row is not None
        original_start = original_row["entry_date"]
        original_end = original_row["exit_date"]
        today_stub = date(2024, 6, 30)

        class _FixedDate(date):
            @classmethod
            def today(cls):  # type: ignore[override]
                return today_stub

        monkeypatch.setattr("app.services.alerts.date", _FixedDate)
        monkeypatch.setattr("app.routes_calendar.date", _FixedDate)

        baseline = phase38_client.get("/api/forecast/2")
        assert baseline.status_code == 200
        assert baseline.get_json()["risk_level"] in {"warning", "danger"}

        response = phase38_client.patch(
            f"/api/trips/{trip_id}",
            json={
                "end_date": "2024-08-15",
                "job_ref": "JOB-BW-EXT",
            },
        )
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["end_date"] == "2024-08-15"
        assert payload["job_ref"] == "JOB-BW-EXT"
        assert payload["duration_days"] >= 76

        with phase38_app.app_context():
            risk = check_alert_status(2)
            assert risk in {"ORANGE", "RED"}

        follow_up = phase38_client.get("/api/forecast/2")
        assert follow_up.status_code == 200
        updated = follow_up.get_json()
        assert updated["risk_level"] == "danger"
        assert updated["projected_total"] >= updated["used_days"]

        revert = phase38_client.patch(
            f"/api/trips/{trip_id}",
            json={
                "start_date": original_start,
                "end_date": original_end,
            },
        )
        assert revert.status_code == 200
