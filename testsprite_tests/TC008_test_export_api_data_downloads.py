import requests

BASE_URL = "http://localhost:5001"
TIMEOUT = 30
HEADERS_JSON = {"Accept": "application/json"}


def test_export_api_data_downloads():
    # Step 1: Create a new employee to use for employee report export
    employee_data = {"name": "Test User For Export"}
    add_employee_url = f"{BASE_URL}/add_employee"
    employee_id = None

    try:
        resp_add = requests.post(add_employee_url, data=employee_data, timeout=TIMEOUT)
        assert resp_add.status_code == 200, f"Failed to add employee, status code: {resp_add.status_code}"
        # Although not explicitly documented, the employee id is expected to be set in Location header or response content
        # We try to retrieve the employee list from /api/employees and find the employee by name to get the id:
        employees_resp = requests.get(f"{BASE_URL}/api/employees", timeout=TIMEOUT)
        assert employees_resp.status_code == 200, "Failed to get employees list"
        employees = employees_resp.json()
        matching_emps = [e for e in employees if e.get("name") == employee_data["name"]]
        assert matching_emps, "Added employee not found in employee list"
        employee_id = matching_emps[0].get("id")
        assert isinstance(employee_id, int), "Invalid employee_id obtained"

        # Step 2: Download trip data CSV
        trip_csv_url = f"{BASE_URL}/export/trips/csv"
        resp_csv = requests.get(trip_csv_url, timeout=TIMEOUT)
        assert resp_csv.status_code == 200, f"Trip CSV export failed with status {resp_csv.status_code}"
        content_type_csv = resp_csv.headers.get("Content-Type", "")
        assert "text/csv" in content_type_csv, f"Incorrect Content-Type for trip CSV export: {content_type_csv}"
        content_csv = resp_csv.content
        assert content_csv.startswith(b"Employee") or b"," in content_csv, "CSV content does not appear valid"

        # Step 3: Download employee report PDF for created employee
        employee_pdf_url = f"{BASE_URL}/export/employee/{employee_id}/pdf"
        resp_pdf_single = requests.get(employee_pdf_url, timeout=TIMEOUT)
        assert resp_pdf_single.status_code == 200, f"Employee PDF export failed with status {resp_pdf_single.status_code}"
        content_type_pdf_single = resp_pdf_single.headers.get("Content-Type", "")
        assert "application/pdf" in content_type_pdf_single, f"Incorrect Content-Type for employee PDF export: {content_type_pdf_single}"
        content_pdf_single = resp_pdf_single.content
        assert content_pdf_single.startswith(b"%PDF") or b"PDF" in content_pdf_single[:10], "PDF content does not appear valid"

        # Step 4: Download all employees report PDF
        all_employees_pdf_url = f"{BASE_URL}/export/all/pdf"
        resp_pdf_all = requests.get(all_employees_pdf_url, timeout=TIMEOUT)
        assert resp_pdf_all.status_code == 200, f"All employees PDF export failed with status {resp_pdf_all.status_code}"
        content_type_pdf_all = resp_pdf_all.headers.get("Content-Type", "")
        assert "application/pdf" in content_type_pdf_all, f"Incorrect Content-Type for all employees PDF export: {content_type_pdf_all}"
        content_pdf_all = resp_pdf_all.content
        assert content_pdf_all.startswith(b"%PDF") or b"PDF" in content_pdf_all[:10], "PDF content does not appear valid"

    finally:
        # Cleanup: delete the created employee if possible
        if employee_id is not None:
            # No explicit delete endpoint documented, so skipping actual deletion
            # If there was a delete, it would be used here
            pass


test_export_api_data_downloads()