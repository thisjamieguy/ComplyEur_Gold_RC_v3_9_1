import requests
import uuid

BASE_URL = "http://localhost:5001"
TIMEOUT = 30

def test_employee_management_api_crud_operations():
    session = requests.Session()

    # Step 1: Add a new employee with valid data
    employee_name = f"Test Employee {uuid.uuid4()}"
    add_emp_url = f"{BASE_URL}/add_employee"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    add_payload = {"name": employee_name}
    try:
        resp = session.post(add_emp_url, data=add_payload, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        assert resp.status_code == 200
        
        # Retrieve employee list to find the ID of the added employee
        list_emp_url = f"{BASE_URL}/api/employees"
        list_resp = session.get(list_emp_url, timeout=TIMEOUT)
        list_resp.raise_for_status()
        assert list_resp.status_code == 200
        employees = list_resp.json()
        # Find employee by name
        employee = next((e for e in employees if e.get("name") == employee_name), None)
        assert employee is not None, "Added employee not found in employee list"
        employee_id = employee.get("id")
        assert isinstance(employee_id, int)

        # Step 2: Retrieve employee details - valid employee_id
        get_emp_url = f"{BASE_URL}/employee/{employee_id}"
        get_resp = session.get(get_emp_url, timeout=TIMEOUT)
        get_resp.raise_for_status()
        assert get_resp.status_code == 200
        # The response should be html or json with employee detail, here we check body presence
        assert get_resp.text and employee_name in get_resp.text

        # Step 3: Retrieve employee details - invalid employee_id (not found)
        invalid_employee_id = 99999999  # Assuming this ID does not exist
        get_invalid_emp_url = f"{BASE_URL}/employee/{invalid_employee_id}"
        invalid_resp = session.get(get_invalid_emp_url, timeout=TIMEOUT)
        assert invalid_resp.status_code == 404

    finally:
        # Cleanup: Delete employee data (GDPR right to erasure)
        # Checking if employee_id was assigned before attempting delete
        if 'employee_id' in locals():
            delete_url = f"{BASE_URL}/admin/dsar/delete/{employee_id}"
            try:
                del_resp = session.post(delete_url, timeout=TIMEOUT)
                # Accept 200 for successful delete or 404 if already removed
                assert del_resp.status_code in (200, 404)
            except Exception:
                pass

test_employee_management_api_crud_operations()
