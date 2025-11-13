#!/usr/bin/env python3
"""
Test forms and button functionality for ComplyEur
Validates all interactive elements work correctly
"""

import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5001"

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

results = {'passed': [], 'failed': [], 'warnings': []}

def test_action(description, test_func):
    """Test wrapper"""
    try:
        success, msg = test_func()
        if success:
            print(f"{GREEN}✓{RESET} {description}")
            results['passed'].append(description)
        else:
            print(f"{RED}✗{RESET} {description} - {msg}")
            results['failed'].append((description, msg))
    except Exception as e:
        print(f"{RED}✗{RESET} {description} - Exception: {str(e)}")
        results['failed'].append((description, str(e)))

print(f"\n{'='*80}")
print(f"ComplyEur Forms & Buttons Testing - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*80}\n")

# Create authenticated session
session = requests.Session()

print(f"{YELLOW}=== Authentication Flow ==={RESET}")
def test_login():
    response = session.post(f"{BASE_URL}/login", data={
        'username': 'admin',
        'password': 'admin123'
    }, allow_redirects=False)
    return response.status_code == 302, f"Status: {response.status_code}"

test_action("Login with valid credentials", test_login)

print(f"\n{YELLOW}=== Dashboard Access ==={RESET}")
def test_dashboard_access():
    response = session.get(f"{BASE_URL}/dashboard")
    return response.status_code == 200, f"Status: {response.status_code}"

test_action("Access dashboard after login", test_dashboard_access)

print(f"\n{YELLOW}=== Employee Management ==={RESET}")
employee_id = None

def test_add_employee():
    global employee_id
    response = session.post(f"{BASE_URL}/add_employee", data={
        'name': 'Test Employee for Forms Test'
    })
    data = response.json()
    if data.get('success'):
        employee_id = data.get('employee_id')
        return True, f"Employee ID: {employee_id}"
    return False, data.get('error', 'Unknown error')

test_action("Add new employee via form", test_add_employee)

def test_employee_detail():
    if not employee_id:
        return False, "No employee ID"
    response = session.get(f"{BASE_URL}/employee/{employee_id}")
    return response.status_code == 200, f"Status: {response.status_code}"

test_action("View employee detail page", test_employee_detail)

print(f"\n{YELLOW}=== Trip Management ==={RESET}")
trip_id = None

def test_add_trip():
    global trip_id
    if not employee_id:
        return False, "No employee ID"
    
    today = datetime.now()
    entry_date = today.strftime('%Y-%m-%d')
    exit_date = (today + timedelta(days=7)).strftime('%Y-%m-%d')
    
    response = session.post(f"{BASE_URL}/add_trip", data={
        'employee_id': employee_id,
        'country_code': 'France',
        'entry_date': entry_date,
        'exit_date': exit_date,
        'purpose': 'Business meeting'
    })
    data = response.json()
    if data.get('success'):
        trip_id = data.get('trip_id')
        return True, f"Trip ID: {trip_id}"
    return False, data.get('error', 'Unknown error')

test_action("Add new trip via form", test_add_trip)

def test_get_trip():
    if not trip_id:
        return False, "No trip ID"
    response = session.get(f"{BASE_URL}/get_trip/{trip_id}")
    data = response.json()
    return 'country' in data, f"Trip data retrieved"

test_action("Get trip details", test_get_trip)

def test_edit_trip():
    if not trip_id:
        return False, "No trip ID"
    
    today = datetime.now()
    entry_date = today.strftime('%Y-%m-%d')
    exit_date = (today + timedelta(days=10)).strftime('%Y-%m-%d')
    
    response = session.post(f"{BASE_URL}/edit_trip/{trip_id}", data={
        'employee_id': employee_id,
        'country_code': 'Germany',
        'entry_date': entry_date,
        'exit_date': exit_date,
        'purpose': 'Updated purpose'
    })
    data = response.json()
    return data.get('success', False), data.get('message', 'No message')

test_action("Edit trip via form", test_edit_trip)

print(f"\n{YELLOW}=== Calendar API ==={RESET}")

def test_calendar_data():
    response = session.get(f"{BASE_URL}/api/calendar_data")
    return response.status_code == 200, f"Status: {response.status_code}"

test_action("Fetch calendar data API", test_calendar_data)

def test_test_calendar_data():
    response = session.get(f"{BASE_URL}/api/test_calendar_data")
    data = response.json()
    return 'resources' in data and 'events' in data, "Calendar structure valid"

test_action("Fetch test calendar data", test_test_calendar_data)

print(f"\n{YELLOW}=== Navigation & Pages ==={RESET}")

def test_what_if_scenario():
    response = session.get(f"{BASE_URL}/what_if_scenario")
    return response.status_code == 200, f"Status: {response.status_code}"

test_action("Access What-If Scenario page", test_what_if_scenario)

def test_future_alerts():
    response = session.get(f"{BASE_URL}/future_job_alerts")
    return response.status_code == 200, f"Status: {response.status_code}"

test_action("Access Future Job Alerts page", test_future_alerts)

def test_bulk_add_trip():
    response = session.get(f"{BASE_URL}/bulk_add_trip")
    return response.status_code == 200, f"Status: {response.status_code}"

test_action("Access Bulk Add Trip page", test_bulk_add_trip)

def test_import_excel():
    response = session.get(f"{BASE_URL}/import_excel")
    return response.status_code == 200, f"Status: {response.status_code}"

test_action("Access Import Excel page", test_import_excel)

print(f"\n{YELLOW}=== Cleanup ==={RESET}")

def test_delete_trip():
    if not trip_id:
        return False, "No trip ID"
    response = session.post(f"{BASE_URL}/delete_trip/{trip_id}")
    data = response.json()
    return data.get('success', False), "Trip deleted"

test_action("Delete test trip", test_delete_trip)

def test_delete_employee():
    if not employee_id:
        return False, "No employee ID"
    response = session.post(f"{BASE_URL}/delete_employee/{employee_id}", allow_redirects=False)
    # Should redirect to dashboard after deletion
    return response.status_code in [200, 302], f"Status: {response.status_code}"

test_action("Delete test employee", test_delete_employee)

# Summary
print(f"\n{'='*80}")
print(f"Test Results Summary")
print(f"{'='*80}")
print(f"{GREEN}Passed:{RESET} {len(results['passed'])}")
print(f"{RED}Failed:{RESET} {len(results['failed'])}")

if results['failed']:
    print(f"\n{RED}Failed Tests:{RESET}")
    for desc, error in results['failed']:
        print(f"  {RED}✗{RESET} {desc} - {error}")

print(f"\n{'='*80}\n")

# Exit with error code if any tests failed
exit(1 if results['failed'] else 0)

