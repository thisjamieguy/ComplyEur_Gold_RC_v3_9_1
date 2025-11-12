import requests
from datetime import date, timedelta

BASE_URL = "http://localhost:5001"
TIMEOUT = 30


def test_calendar_api_trip_operations_and_filters():
    session = requests.Session()

    # Step 1: List all employees via /api/employees
    employees_resp = session.get(f"{BASE_URL}/api/employees", timeout=TIMEOUT)
    assert employees_resp.status_code == 200
    employees_data = employees_resp.json()
    assert isinstance(employees_data, list)
    # Ensure employees have id, name, active
    assert all("id" in e and "name" in e and "active" in e for e in employees_data)
    assert len(employees_data) > 0, "No employees found to test with"
    employee_id = employees_data[0]["id"]

    # Step 2: Retrieve trips with optional date filters via /api/trips?start=...&end=...
    # Use a date range that covers at least some time
    start_filter = (date.today() - timedelta(days=180)).isoformat()
    end_filter = date.today().isoformat()
    trips_resp = session.get(f"{BASE_URL}/api/trips", params={"start": start_filter, "end": end_filter}, timeout=TIMEOUT)
    assert trips_resp.status_code == 200
    trips_data = trips_resp.json()
    # Expect keys: employees (array), trips (array), alerts (array)
    assert isinstance(trips_data, dict)
    assert "employees" in trips_data and "trips" in trips_data and "alerts" in trips_data
    assert isinstance(trips_data["employees"], list)
    assert isinstance(trips_data["trips"], list)
    assert isinstance(trips_data["alerts"], list)

    # --- Create a new trip because we need a trip ID for update, delete and duplicate tests ---
    new_trip_payload = {
        "employee_id": employee_id,
        "country": "FR",
        "start_date": (date.today() + timedelta(days=1)).isoformat(),
        "end_date": (date.today() + timedelta(days=5)).isoformat(),
    }
    create_resp = session.post(f"{BASE_URL}/api/trips", json=new_trip_payload, timeout=TIMEOUT)
    assert create_resp.status_code == 201
    created_trip = create_resp.json()
    # Trip creation might return full trip object or at least contain 'id'
    # If no body or id, fallback to retrieving trips to find latest, but here we assume id in json
    trip_id = created_trip.get("id")
    assert trip_id is not None, "Created trip ID not returned."

    try:
        # Step 3: Update trip via PATCH /api/trips/{trip_id}
        update_payload = {
            "country": "DE",
            "start_date": new_trip_payload["start_date"],
            "end_date": (date.today() + timedelta(days=6)).isoformat(),
        }
        update_resp = session.patch(f"{BASE_URL}/api/trips/{trip_id}", json=update_payload, timeout=TIMEOUT)
        assert update_resp.status_code == 200

        # Step 4: Get trip by ID GET /api/trips/{trip_id}
        get_trip_resp = session.get(f"{BASE_URL}/api/trips/{trip_id}", timeout=TIMEOUT)
        assert get_trip_resp.status_code == 200
        trip_detail = get_trip_resp.json()
        assert trip_detail["id"] == trip_id
        assert trip_detail["country"] == update_payload["country"]
        assert trip_detail["start_date"] == update_payload["start_date"]
        assert trip_detail["end_date"] == update_payload["end_date"]

        # Step 5: Duplicate trip POST /api/trips/{trip_id}/duplicate
        duplicate_resp = session.post(f"{BASE_URL}/api/trips/{trip_id}/duplicate", timeout=TIMEOUT)
        assert duplicate_resp.status_code == 201
        duplicated_trip = duplicate_resp.json()
        duplicated_trip_id = duplicated_trip.get("id")
        assert duplicated_trip_id is not None
        assert duplicated_trip_id != trip_id

        # Cleanup duplicated trip
        del_dup_resp = session.delete(f"{BASE_URL}/api/trips/{duplicated_trip_id}", timeout=TIMEOUT)
        assert del_dup_resp.status_code == 200

        # Step 6: Fetch compliance forecast for employee GET /api/forecast/{employee_id}
        forecast_resp = session.get(f"{BASE_URL}/api/forecast/{employee_id}", timeout=TIMEOUT)
        assert forecast_resp.status_code == 200
        forecast_data = forecast_resp.json()
        # Validate forecast keys and types
        assert "used_days" in forecast_data and isinstance(forecast_data["used_days"], int)
        assert "upcoming_days" in forecast_data and isinstance(forecast_data["upcoming_days"], int)
        assert "projected_total" in forecast_data and isinstance(forecast_data["projected_total"], int)
        assert "risk_level" in forecast_data and isinstance(forecast_data["risk_level"], str)

        # Step 7: Fetch active compliance alerts via /api/alerts
        alerts_resp = session.get(f"{BASE_URL}/api/alerts", timeout=TIMEOUT)
        assert alerts_resp.status_code == 200
        alerts_data = alerts_resp.json()
        assert "alerts" in alerts_data and isinstance(alerts_data["alerts"], list)

        # Optionally test alerts filter by risk (if any alerts exist)
        if alerts_data["alerts"]:
            risk_level = alerts_data["alerts"][0].get("risk_level")
            if risk_level:
                alerts_filtered_resp = session.get(f"{BASE_URL}/api/alerts", params={"risk": risk_level}, timeout=TIMEOUT)
                assert alerts_filtered_resp.status_code == 200
                filtered_alerts = alerts_filtered_resp.json()
                assert "alerts" in filtered_alerts

    finally:
        # Step 8: Delete created trip DELETE /api/trips/{trip_id}
        del_resp = session.delete(f"{BASE_URL}/api/trips/{trip_id}", timeout=TIMEOUT)
        # Allow 200 or 404 if already deleted by duplicate test cleanup
        assert del_resp.status_code in [200, 404]


test_calendar_api_trip_operations_and_filters()