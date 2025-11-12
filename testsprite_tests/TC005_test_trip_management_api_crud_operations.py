import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5001"
TIMEOUT = 30

def test_trip_management_api_crud_operations():
    session = requests.Session()
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    employee_id = None
    trip_ids = []

    def create_employee(name="Test Employee for Trip"):
        resp = session.post(f"{BASE_URL}/add_employee", data={"name": name}, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        # After adding employee, fetch employees to find the ID
        emp_list = session.get(f"{BASE_URL}/api/employees", timeout=TIMEOUT)
        emp_list.raise_for_status()
        employees = emp_list.json()
        for emp in employees:
            if emp.get("name") == name:
                return emp.get("id")
        raise Exception("Failed to create/find employee")

    def delete_trip(trip_id):
        resp = session.post(f"{BASE_URL}/delete_trip/{trip_id}", headers=headers, timeout=TIMEOUT)
        if resp.status_code not in (200, 404):
            resp.raise_for_status()

    def delete_employee(emp_id):
        # Delete employee by GDPR DSAR delete endpoint
        resp = session.post(f"{BASE_URL}/admin/dsar/delete/{emp_id}", headers=headers, timeout=TIMEOUT)
        if resp.status_code not in (200, 404):
            resp.raise_for_status()

    def add_trip(data):
        resp = session.post(f"{BASE_URL}/add_trip", data=data, headers=headers, timeout=TIMEOUT)
        return resp

    def edit_trip(trip_id, data):
        resp = session.post(f"{BASE_URL}/edit_trip/{trip_id}", data=data, headers=headers, timeout=TIMEOUT)
        return resp

    try:
        # Step 1: Create an employee
        employee_id = create_employee()

        # Dates for trips
        today = datetime.utcnow().date()
        past_entry = (today - timedelta(days=20)).isoformat()
        past_exit = (today - timedelta(days=10)).isoformat()
        ongoing_entry = (today - timedelta(days=2)).isoformat()
        ongoing_exit = (today + timedelta(days=5)).isoformat()
        overlapping_entry = (today - timedelta(days=15)).isoformat()
        overlapping_exit = (today - timedelta(days=5)).isoformat()
        future_entry = (today + timedelta(days=6)).isoformat()
        future_exit = (today + timedelta(days=10)).isoformat()
        invalid_entry = (today + timedelta(days=10)).isoformat()
        invalid_exit = (today + timedelta(days=1)).isoformat()  # exit before entry

        # Step 2: Add a valid past trip
        trip_data_1 = {
            "employee_id": employee_id,
            "country": "France",
            "entry_date": past_entry,
            "exit_date": past_exit,
            "purpose": "Business"
        }
        resp = add_trip(trip_data_1)
        assert resp.status_code == 200, f"Failed to add valid past trip: {resp.text}"
        resp_json = resp.json() if resp.headers.get('Content-Type', '').startswith('application/json') else {}
        # ID might not be in response - fetch trips to find it
        trips_resp = session.get(f"{BASE_URL}/api/trips", timeout=TIMEOUT)
        trips_resp.raise_for_status()
        trips = trips_resp.json().get("trips", [])
        trip_1 = next((t for t in trips if t["employee_id"] == employee_id and t["entry_date"] == past_entry and t["exit_date"] == past_exit), None)
        assert trip_1 is not None, "Added trip not found in trip list"
        trip_1_id = trip_1["id"]
        trip_ids.append(trip_1_id)

        # Step 3: Add an ongoing trip (entry date in past, exit date in future)
        trip_data_ongoing = {
            "employee_id": employee_id,
            "country": "Germany",
            "entry_date": ongoing_entry,
            "exit_date": ongoing_exit,
            "purpose": "Conference"
        }
        resp = add_trip(trip_data_ongoing)
        assert resp.status_code == 200, f"Failed to add ongoing trip: {resp.text}"
        trips_resp = session.get(f"{BASE_URL}/api/trips", timeout=TIMEOUT)
        trips_resp.raise_for_status()
        trips = trips_resp.json().get("trips", [])
        trip_ongoing = next((t for t in trips if t["employee_id"] == employee_id and t["entry_date"] == ongoing_entry and t["exit_date"] == ongoing_exit), None)
        assert trip_ongoing is not None, "Added ongoing trip not found"
        trip_ongoing_id = trip_ongoing["id"]
        trip_ids.append(trip_ongoing_id)

        # Step 4: Attempt to add overlapping trip for same employee - expect failure or validation
        overlapping_trip_data = {
            "employee_id": employee_id,
            "country": "Italy",
            "entry_date": overlapping_entry,
            "exit_date": overlapping_exit,
            "purpose": "Vacation"
        }
        resp = add_trip(overlapping_trip_data)
        # This can be either a validation error or success depending on business rule enforced by backend
        # We'll assert that either 400 or 200 response is received and if 200, the trip must not overlap logically
        if resp.status_code == 200:
            trips_resp = session.get(f"{BASE_URL}/api/trips", timeout=TIMEOUT)
            trips_resp.raise_for_status()
            trips = trips_resp.json().get("trips", [])
            trip_overlap = next((t for t in trips if t["employee_id"] == employee_id and t["entry_date"] == overlapping_entry and t["exit_date"] == overlapping_exit), None)
            assert trip_overlap is None, "Overlapping trip was incorrectly added"
        else:
            assert resp.status_code == 400 or resp.status_code == 409, f"Unexpected status for overlapping trip: {resp.status_code}, {resp.text}"

        # Step 5: Add a future trip after ongoing (non-overlapping allowed)
        future_trip_data = {
            "employee_id": employee_id,
            "country": "Spain",
            "entry_date": future_entry,
            "exit_date": future_exit,
            "purpose": "Training"
        }
        resp = add_trip(future_trip_data)
        assert resp.status_code == 200, f"Failed to add valid future trip: {resp.text}"
        trips_resp = session.get(f"{BASE_URL}/api/trips", timeout=TIMEOUT)
        trips_resp.raise_for_status()
        trips = trips_resp.json().get("trips", [])
        trip_future = next((t for t in trips if t["employee_id"] == employee_id and t["entry_date"] == future_entry and t["exit_date"] == future_exit), None)
        assert trip_future is not None, "Added future trip not found"
        trip_future_id = trip_future["id"]
        trip_ids.append(trip_future_id)

        # Step 6: Try to add trip with invalid date range (exit before entry) - expect 400
        invalid_trip_data = {
            "employee_id": employee_id,
            "country": "Netherlands",
            "entry_date": invalid_entry,
            "exit_date": invalid_exit,
            "purpose": "Invalid"
        }
        resp = add_trip(invalid_trip_data)
        assert resp.status_code == 400, f"Invalid trip date range should fail with 400 but got {resp.status_code}"

        # Step 7: Edit an existing trip with a valid update (change country)
        new_country = "Belgium"
        edit_data = {
            "country": new_country,
            "entry_date": past_entry,
            "exit_date": past_exit
        }
        resp = edit_trip(trip_1_id, edit_data)
        assert resp.status_code == 200, f"Failed to edit trip: {resp.text}"

        # Verify edit
        resp = session.get(f"{BASE_URL}/api/trips/{trip_1_id}", timeout=TIMEOUT)
        if resp.status_code == 404:
            raise AssertionError("Edited trip not found after update")
        resp.raise_for_status()
        trip_details = resp.json()
        assert trip_details.get("country") == new_country, "Trip country not updated correctly"

        # Step 8: Edit trip with invalid data (exit date before entry) - expect error
        invalid_edit_data = {
            "country": "USA",
            "entry_date": invalid_entry,
            "exit_date": invalid_exit
        }
        resp = edit_trip(trip_1_id, invalid_edit_data)
        assert resp.status_code == 400 or resp.status_code == 422, f"Invalid edit did not return expected error, got {resp.status_code}"

        # Step 9: Delete a trip
        resp = session.delete(f"{BASE_URL}/api/trips/{trip_future_id}", timeout=TIMEOUT)
        if resp.status_code == 404:
            # fallback to legacy post delete endpoint
            resp_del_post = session.post(f"{BASE_URL}/delete_trip/{trip_future_id}", headers=headers, timeout=TIMEOUT)
            assert resp_del_post.status_code == 200 or resp_del_post.status_code == 404, "Failed to delete trip with fallback endpoint"
        else:
            assert resp.status_code == 200, "Failed to delete future trip"

        # Verify deletion
        resp_check = session.get(f"{BASE_URL}/api/trips/{trip_future_id}", timeout=TIMEOUT)
        assert resp_check.status_code == 404, "Deleted trip still retrievable"

    finally:
        # Cleanup: delete created trips and employee
        for tid in trip_ids:
            try:
                session.delete(f"{BASE_URL}/api/trips/{tid}", timeout=TIMEOUT)
            except Exception:
                try:
                    session.post(f"{BASE_URL}/delete_trip/{tid}", headers=headers, timeout=TIMEOUT)
                except Exception:
                    pass
        if employee_id:
            try:
                delete_employee(employee_id)
            except Exception:
                pass

test_trip_management_api_crud_operations()