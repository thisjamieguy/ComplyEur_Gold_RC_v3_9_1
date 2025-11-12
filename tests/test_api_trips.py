"""Tests for /api/trips endpoints."""

def test_trip_create_list_flow(auth_client):
    """Test trip creation and listing flow."""
    # create employee
    er = auth_client.post("/api/employees", json={"name": "Bob"})
    assert er.status_code == 201
    eid = er.get_json()["id"]
    
    # create trip for Bob
    tr = auth_client.post("/api/trips", json={
        "employee_id": eid,
        "country": "FR",
        "start_date": "2025-01-10",
        "end_date": "2025-01-20"
    })
    assert tr.status_code == 201
    
    # list trips
    lr = auth_client.get("/api/trips")
    assert lr.status_code == 200
    trips = lr.get_json()
    assert any(t["employee_id"] == eid for t in trips)
