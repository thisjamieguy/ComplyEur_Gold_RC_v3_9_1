#!/usr/bin/env python3
"""
Comprehensive route tester for ComplyEur
Tests all routes and identifies any 500 errors or broken endpoints
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5001"
session = requests.Session()

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

# Track results
results = {
    'passed': [],
    'failed': [],
    'warnings': []
}

def test_route(method, path, expected_status=200, data=None, description="", requires_auth=False):
    """Test a single route"""
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            response = session.get(url, allow_redirects=False, timeout=5)
        elif method == "POST":
            response = session.post(url, json=data, allow_redirects=False, timeout=5)
        elif method == "PATCH":
            response = session.patch(url, json=data, allow_redirects=False, timeout=5)
        elif method == "DELETE":
            response = session.delete(url, allow_redirects=False, timeout=5)
        else:
            print(f"{RED}✗{RESET} {method} {path} - Unknown method")
            results['failed'].append((method, path, "Unknown method"))
            return
        
        # Check for 500 errors
        if response.status_code == 500:
            print(f"{RED}✗ 500 ERROR{RESET} {method} {path} {description}")
            results['failed'].append((method, path, f"500 Internal Server Error"))
            return
        
        # Check for expected status or acceptable alternatives
        acceptable_statuses = [expected_status]
        if requires_auth:
            acceptable_statuses.extend([302, 401, 403])  # Redirects or auth errors are ok
        
        if response.status_code in acceptable_statuses:
            print(f"{GREEN}✓{RESET} {method} {path} [{response.status_code}] {description}")
            results['passed'].append((method, path, response.status_code))
        elif response.status_code == 404:
            print(f"{RED}✗ 404{RESET} {method} {path} - Route not found {description}")
            results['failed'].append((method, path, "404 Not Found"))
        elif response.status_code in [301, 302, 303, 307, 308]:
            print(f"{YELLOW}⟳{RESET} {method} {path} [{response.status_code} → {response.headers.get('Location', 'unknown')}] {description}")
            results['warnings'].append((method, path, f"Redirect to {response.headers.get('Location', 'unknown')}"))
        else:
            print(f"{YELLOW}⚠{RESET} {method} {path} [{response.status_code}] {description}")
            results['warnings'].append((method, path, f"Unexpected status {response.status_code}"))
    except requests.exceptions.Timeout:
        print(f"{RED}✗ TIMEOUT{RESET} {method} {path} {description}")
        results['failed'].append((method, path, "Timeout"))
    except Exception as e:
        print(f"{RED}✗ ERROR{RESET} {method} {path} - {str(e)} {description}")
        results['failed'].append((method, path, str(e)))

print(f"\n{'='*80}")
print(f"ComplyEur Route Testing - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*80}\n")

# Health & Info Routes
print(f"\n{YELLOW}=== Health & Info Routes ==={RESET}")
test_route("GET", "/health", 200, description="Health check")
test_route("GET", "/health/live", 200, description="Liveness probe")
test_route("GET", "/health/ready", 200, description="Readiness probe")
test_route("GET", "/healthz", 200, description="Healthz probe")
test_route("GET", "/api/version", 200, description="API version")

# Public Routes
print(f"\n{YELLOW}=== Public Routes ==={RESET}")
test_route("GET", "/", 200, description="Landing page")
test_route("GET", "/landing", 200, description="Landing page alt")
test_route("GET", "/privacy", 200, description="Privacy policy")
test_route("GET", "/privacy-policy", 200, description="Privacy policy alt")
test_route("GET", "/cookie-policy", 200, description="Cookie policy")
test_route("GET", "/sitemap.xml", 200, description="Sitemap")
test_route("GET", "/robots.txt", 200, description="Robots.txt")
test_route("GET", "/help", 200, description="Help page")
test_route("GET", "/entry-requirements", 200, description="Entry requirements")

# Auth Routes (expect redirects or 200)
print(f"\n{YELLOW}=== Auth Routes ==={RESET}")
test_route("GET", "/login", 200, description="Login page")
test_route("GET", "/signup", 200, description="Signup page")
test_route("GET", "/get-started", 200, description="Get started")
test_route("GET", "/logout", 302, description="Logout (expects redirect)")

# Protected Routes (expect redirects to login or 200 if logged in)
print(f"\n{YELLOW}=== Protected Routes (Dashboard & Main) ==={RESET}")
test_route("GET", "/dashboard", 200, requires_auth=True, description="Dashboard")
test_route("GET", "/calendar", 200, requires_auth=True, description="Calendar")
test_route("GET", "/calendar_view", 200, requires_auth=True, description="Calendar view")
test_route("GET", "/global_calendar", 200, requires_auth=True, description="Global calendar")
test_route("GET", "/profile", 200, requires_auth=True, description="Profile")
test_route("GET", "/home", 200, requires_auth=True, description="Home")

# Trip Management Routes
print(f"\n{YELLOW}=== Trip Management Routes ==={RESET}")
test_route("GET", "/bulk_add_trip", 200, requires_auth=True, description="Bulk add trip")
test_route("GET", "/import_excel", 200, requires_auth=True, description="Import Excel")
test_route("GET", "/what_if_scenario", 200, requires_auth=True, description="What-if scenario")
test_route("GET", "/future_job_alerts", 200, requires_auth=True, description="Future job alerts")
test_route("GET", "/export_future_alerts", 200, requires_auth=True, description="Export alerts")
test_route("GET", "/export/trips/csv", 200, requires_auth=True, description="Export trips CSV")

# Admin Routes
print(f"\n{YELLOW}=== Admin Routes ==={RESET}")
test_route("GET", "/admin_settings", 200, requires_auth=True, description="Admin settings")
test_route("GET", "/admin_privacy_tools", 200, requires_auth=True, description="Privacy tools (legacy)")
test_route("GET", "/admin/privacy-tools", 200, requires_auth=True, description="Privacy tools")
test_route("GET", "/admin/retention/expired", 200, requires_auth=True, description="Expired trips")
test_route("GET", "/admin/audit-trail", 200, requires_auth=True, description="Audit trail")

# API Routes - Employee
print(f"\n{YELLOW}=== API Routes - Employees ==={RESET}")
test_route("GET", "/api/employees", 200, requires_auth=True, description="List employees")
test_route("GET", "/api/employees/search", 200, requires_auth=True, description="Search employees")

# API Routes - Trips
print(f"\n{YELLOW}=== API Routes - Trips ==={RESET}")
test_route("GET", "/api/trips", 200, requires_auth=True, description="List trips")
test_route("GET", "/api/calendar_data", 200, requires_auth=True, description="Calendar data")
test_route("GET", "/api/test_calendar_data", 200, requires_auth=True, description="Test calendar data")

# API Routes - Entry Requirements
print(f"\n{YELLOW}=== API Routes - Entry Requirements ==={RESET}")
test_route("GET", "/api/entry-requirements", 200, description="Entry requirements API")

# API Routes - Testing
print(f"\n{YELLOW}=== API Routes - Testing ==={RESET}")
test_route("GET", "/api/test", 200, description="API test endpoint")
test_route("GET", "/api/test_session", 200, description="Session test")

# API Routes - Audit
print(f"\n{YELLOW}=== API Routes - Audit ==={RESET}")
test_route("GET", "/api/audit-trail", 200, requires_auth=True, description="Audit trail API")
test_route("GET", "/api/audit-trail/stats", 200, requires_auth=True, description="Audit stats")

# API Routes - Retention
print(f"\n{YELLOW}=== API Routes - Retention/Privacy ==={RESET}")
test_route("GET", "/api/retention/preview", 200, requires_auth=True, description="Retention preview")

# Error pages
print(f"\n{YELLOW}=== Error Pages ==={RESET}")
test_route("GET", "/this-route-does-not-exist-404", 404, description="404 error page")

# Summary
print(f"\n{'='*80}")
print(f"Test Results Summary")
print(f"{'='*80}")
print(f"{GREEN}Passed:{RESET} {len(results['passed'])}")
print(f"{YELLOW}Warnings:{RESET} {len(results['warnings'])}")
print(f"{RED}Failed:{RESET} {len(results['failed'])}")

if results['failed']:
    print(f"\n{RED}Failed Routes:{RESET}")
    for method, path, error in results['failed']:
        print(f"  {RED}✗{RESET} {method} {path} - {error}")

if results['warnings']:
    print(f"\n{YELLOW}Warnings:{RESET}")
    for method, path, msg in results['warnings']:
        print(f"  {YELLOW}⚠{RESET} {method} {path} - {msg}")

print(f"\n{'='*80}\n")

# Exit with error code if any routes failed
exit(1 if results['failed'] else 0)

