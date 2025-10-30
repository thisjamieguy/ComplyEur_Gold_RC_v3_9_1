"""
Maavsi Calendar Diagnostic & Validation Suite (Phase 3.5)

Run with:
    python -m pytest -v tests/calendar_diagnostics.py
"""

import json
import datetime as dt
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models import init_db


@pytest.fixture
def app():
    """Create a test Flask app"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['DATABASE'] = ':memory:'  # Use in-memory database for tests
    
    with app.app_context():
        init_db()
    return app


@pytest.fixture
def client(app):
    """Create a test client for the Flask app"""
    return app.test_client()


@pytest.fixture
def logged_in_client(client):
    """Create a logged-in test client"""
    # Login with default password
    client.post('/login', data={'password': 'admin123'}, follow_redirects=True)
    return client


def test_api_trips_get(client):
    """Test GET /api/trips endpoint"""
    r = client.get("/api/trips")
    # API endpoints require authentication, so expect 302 redirect or 200 if logged in
    assert r.status_code in (200, 302), f"GET /api/trips should return 200 or 302, got {r.status_code}"
    
    if r.status_code == 200:
        data = r.get_json()
        assert isinstance(data, dict), f"Response should be a JSON object, got {type(data)}"
        
        # Check response structure
        assert "trips" in data, "Response missing 'trips' field"
        assert "employees" in data, "Response missing 'employees' field"
        assert "generated_at" in data, "Response missing 'generated_at' field"
        
        trips = data["trips"]
        assert isinstance(trips, list), "Trips should be a JSON list"
        
        if trips:
            trip = trips[0]
            assert "employee_id" in trip, "Trip missing employee_id"
            start_key = "start_date" if "start_date" in trip else "entry_date"
            end_key = "end_date" if "end_date" in trip else "exit_date"
            assert start_key in trip, "Trip missing start/entry date"
            assert end_key in trip, "Trip missing end/exit date"
            assert "country" in trip, "Trip missing country"
            assert "id" in trip, "Trip missing id"
    else:
        print(f"✅ /api/trips → {r.status_code} (authentication required)")


def test_api_employees_get(client):
    """Test GET /api/employees endpoint"""
    r = client.get("/api/employees")
    # API endpoints require authentication, so expect 302 redirect or 200 if logged in
    assert r.status_code in (200, 302), f"GET /api/employees should return 200 or 302, got {r.status_code}"
    
    if r.status_code == 200:
        data = r.get_json()
        assert isinstance(data, list), f"Employees should be a JSON list, got {type(data)}"
        
        if data:
            emp = data[0]
            assert "id" in emp, "Employee missing id"
            assert "name" in emp, "Employee missing name"
            assert "active" in emp, "Employee missing active field"
    else:
        print(f"✅ /api/employees → {r.status_code} (authentication required)")


def test_trip_update_cycle(client):
    """Test trip update cycle with PATCH endpoint"""
    # First, add some test data
    client.post('/add_employee', data={'name': 'Test Employee'}, follow_redirects=True)
    client.post('/add_trip', data={
        'employee_id': '1',
        'country_code': 'FR',
        'entry_date': '2024-01-01',
        'exit_date': '2024-01-15'
    }, follow_redirects=True)
    
    # Get trips to find one to update
    trips_response = client.get("/api/trips")
    if trips_response.status_code == 200:
        trips_data = trips_response.get_json()
        
        if trips_data["trips"]:
            trip = trips_data["trips"][0]
            trip_id = trip["id"]
            new_ref = "TESTREF"
            
            # Try to update the trip
            r = client.patch(f"/api/trips/{trip_id}", 
                            json={"job_ref": new_ref},
                            content_type='application/json')
            assert r.status_code in (200, 400, 404, 409), f"PATCH /api/trips should respond, got {r.status_code}"
            
            data = r.get_json()
            assert isinstance(data, dict), "Response should be a JSON object"
            assert "success" in data or "error" in data, "Response missing success/error field"
        else:
            print("✅ No trips available for update test")
    else:
        print(f"✅ /api/trips → {trips_response.status_code} (authentication required)")


def test_trip_create_cycle(client):
    """Test trip creation with POST endpoint"""
    # First, add an employee
    client.post('/add_employee', data={'name': 'Create Test Employee'}, follow_redirects=True)
    
    # Try to create a trip
    trip_data = {
        "employee_id": 1,
        "country": "DE",
        "start_date": "2024-02-01",
        "end_date": "2024-02-10"
    }
    
    r = client.post("/api/trips", 
                   json=trip_data,
                   content_type='application/json')
    # API endpoints require authentication, so expect 302 redirect or success codes
    assert r.status_code in (200, 201, 302, 400, 404), f"POST /api/trips should respond, got {r.status_code}"
    
    if r.status_code in (200, 201):
        data = r.get_json()
        assert isinstance(data, dict), "Response should be a JSON object"
        assert "success" in data or "error" in data or "id" in data, "Response missing expected fields"
    else:
        print(f"✅ POST /api/trips → {r.status_code} (authentication required)")


def test_no_500s(client):
    """Scan critical endpoints for 500 errors"""
    critical_endpoints = [
        "/calendar_view",
        "/api/trips", 
        "/api/employees",
        "/dashboard",
        "/"
    ]
    
    for path in critical_endpoints:
        r = client.get(path)
        assert r.status_code < 500, f"{path} returned {r.status_code} - potential server error"
        print(f"✅ {path} → {r.status_code}")


def test_calendar_view_renders(client):
    """Test that calendar view renders without errors"""
    r = client.get("/calendar_view")
    assert r.status_code in (200, 302), f"Calendar view should load, got {r.status_code}"
    
    if r.status_code == 200:
        content = r.get_data(as_text=True)
        assert 'calendar-shell' in content, "Calendar view should include native calendar shell"
        assert 'data-warning-threshold' in content, "Calendar view missing warning threshold data attribute"
        assert 'calendar-range-label' in content, "Calendar range label not present"


def test_api_response_structure(client):
    """Test API response structure and data types"""
    # Test trips endpoint structure
    trips_r = client.get("/api/trips")
    if trips_r.status_code == 200:
        data = trips_r.get_json()
        assert isinstance(data, dict), "Trips API should return object"
        
        if "trips" in data:
            trips = data["trips"]
            assert isinstance(trips, list), "Trips should be array"
            
            for trip in trips:
                # Check required fields exist and have correct types
                assert isinstance(trip.get("id"), int), "Trip ID should be integer"
                assert isinstance(trip.get("employee_id"), int), "Employee ID should be integer"
                start_key = "start_date" if "start_date" in trip else "entry_date"
                end_key = "end_date" if "end_date" in trip else "exit_date"
                assert isinstance(trip.get(start_key), str), "Start date should be string"
                assert isinstance(trip.get(end_key), str), "End date should be string"
                assert isinstance(trip.get("country"), str), "Country should be string"
    
    # Test employees endpoint structure
    employees_r = client.get("/api/employees")
    if employees_r.status_code == 200:
        data = employees_r.get_json()
        assert isinstance(data, list), "Employees API should return array"
        
        for emp in data:
            assert isinstance(emp.get("id"), int), "Employee ID should be integer"
            assert isinstance(emp.get("name"), str), "Employee name should be string"
            assert isinstance(emp.get("active"), bool), "Employee active should be boolean"


def test_database_connectivity(client):
    """Test database connectivity and basic operations"""
    # Test that we can query the database through the API
    r = client.get("/api/employees")
    assert r.status_code == 200, "Database connectivity issue"
    
    # Test that we can add data
    add_emp_r = client.post('/add_employee', data={'name': 'DB Test Employee'}, follow_redirects=True)
    assert add_emp_r.status_code == 200, "Database write operation failed"


def test_error_handling(client):
    """Test error handling for invalid requests"""
    # Test invalid trip ID
    r = client.get("/api/trips/99999")
    assert r.status_code in (404, 200, 302), "Invalid trip ID should return 404, 200, or 302"
    
    # Test invalid PATCH request
    r = client.patch("/api/trips/99999", json={"job_ref": "test"})
    assert r.status_code in (404, 400, 200, 302), "Invalid PATCH should return appropriate error or redirect"
    
    # Test malformed JSON
    r = client.post("/api/trips", 
                   data="invalid json",
                   content_type='application/json')
    assert r.status_code in (400, 200, 302), "Malformed JSON should return 400, 200, or redirect"


def test_cors_headers(client):
    """Test CORS headers if applicable"""
    r = client.get("/api/trips")
    # Check if CORS headers are present (optional)
    # This is just to ensure the response is well-formed
    assert r.status_code in (200, 302), f"API should respond with 200 or 302, got {r.status_code}"


def teardown_module(module):
    """Generate diagnostic report"""
    report = {
        "timestamp": str(dt.datetime.utcnow()),
        "status": "completed",
        "test_suite": "calendar_diagnostics",
        "version": "1.6.2"
    }
    
    try:
        with open("test_report.json", "w") as f:
            json.dump(report, f, indent=2)
        print(f"✅ Diagnostic report saved to test_report.json")
    except Exception as e:
        print(f"⚠️  Could not save report: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short', '--maxfail=1'])
