import requests

BASE_URL = "http://localhost:5001"
TIMEOUT = 30

def test_admin_dsar_api_gdpr_data_management():
    session = requests.Session()
    employee_id = None
    try:
        # Step 1: Create a new employee (needed for DSAR operations)
        add_employee_url = f"{BASE_URL}/add_employee"
        new_employee_name = "GDPR Test Employee"
        add_resp = session.post(
            add_employee_url,
            data={"name": new_employee_name},
            timeout=TIMEOUT
        )
        assert add_resp.status_code == 200, "Failed to add new employee"
        # The response presumably contains redirect or success message but no ID; obtain by searching employees
        # Since no direct get all employees in add_employee, try API employees list
        employees_resp = session.get(f"{BASE_URL}/api/employees", timeout=TIMEOUT)
        assert employees_resp.status_code == 200, "Failed to list employees"
        employees = employees_resp.json()
        # Find employee by name
        matched = [e for e in employees if e.get("name") == new_employee_name]
        assert matched, "Newly added employee not found in employees list"
        employee_id = matched[0]["id"]

        # Step 2: Export employee data as DSAR ZIP
        export_url = f"{BASE_URL}/admin/dsar/export/{employee_id}"
        export_resp = session.get(export_url, timeout=TIMEOUT)
        assert export_resp.status_code == 200, "Failed to export DSAR ZIP"
        content_type = export_resp.headers.get("Content-Type", "")
        assert "application/zip" in content_type, f"Unexpected content type for DSAR export: {content_type}"
        content_length = export_resp.headers.get("Content-Length")
        assert content_length is None or int(content_length) > 0, "Empty content in DSAR export"

        # Step 3: Rectify employee name
        rectify_url = f"{BASE_URL}/admin/dsar/rectify/{employee_id}"
        new_name = "GDPR Test Employee Rectified"
        rectify_resp = session.post(
            rectify_url,
            data={"name": new_name},
            timeout=TIMEOUT
        )
        assert rectify_resp.status_code == 200, "Failed to rectify employee name"
        # Verify rectification by re-fetching employee details
        get_employee_url = f"{BASE_URL}/employee/{employee_id}"
        get_emp_resp = session.get(get_employee_url, timeout=TIMEOUT)
        assert get_emp_resp.status_code == 200, "Failed to fetch employee details after rectification"
        assert new_name in get_emp_resp.text, "Employee name not updated after rectification"

        # Step 4: Anonymize employee data
        anonymize_url = f"{BASE_URL}/admin/dsar/anonymize/{employee_id}"
        anonymize_resp = session.post(anonymize_url, timeout=TIMEOUT)
        assert anonymize_resp.status_code == 200, "Failed to anonymize employee data"
        # Verify anonymization by fetching employee details and checking name is anonymized (not equal to previous)
        get_emp_post_anon_resp = session.get(get_employee_url, timeout=TIMEOUT)
        assert get_emp_post_anon_resp.status_code == 200, "Failed to fetch employee after anonymization"
        # Name should not be the rectified name; minimally check rectified name absent
        assert new_name not in get_emp_post_anon_resp.text, "Employee name not anonymized"

        # Step 5: Delete employee data
        delete_url = f"{BASE_URL}/admin/dsar/delete/{employee_id}"
        delete_resp = session.post(delete_url, timeout=TIMEOUT)
        assert delete_resp.status_code == 200, "Failed to delete employee data"

        # Step 6: Confirm deletion: employee detail should return 404 or equivalent
        get_emp_after_delete_resp = session.get(get_employee_url, timeout=TIMEOUT)
        assert get_emp_after_delete_resp.status_code == 404 or get_emp_after_delete_resp.status_code == 200 and "not found" in get_emp_after_delete_resp.text.lower(), "Employee data still exists after deletion"
    finally:
        # Cleanup in case employee data was not deleted
        if employee_id is not None:
            # Try delete again to clean up
            try:
                session.post(f"{BASE_URL}/admin/dsar/delete/{employee_id}", timeout=TIMEOUT)
            except Exception:
                pass

test_admin_dsar_api_gdpr_data_management()