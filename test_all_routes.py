#!/usr/bin/env python3
"""
Comprehensive route tester for ComplyEur
Tests all routes and identifies any 500 errors or broken endpoints
"""

import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple

BASE_URL = "http://localhost:5001"

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'


def run_all_routes(base_url: str = BASE_URL, session_obj: Optional[requests.Session] = None) -> Dict[str, List[Tuple[str, str, str]]]:
    """Execute the full route scan and return structured results without exiting."""
    session = session_obj or requests.Session()
    results = {
        'passed': [],
        'failed': [],
        'warnings': []
    }

    def test_route(method, path, expected_status=200, data=None, description="", requires_auth=False):
        """Test a single route"""
        url = f"{base_url}{path}"
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
            
            if response.status_code == 500:
                print(f"{RED}✗ 500 ERROR{RESET} {method} {path} {description}")
                results['failed'].append((method, path, "500 Internal Server Error"))
                return
            
            acceptable_statuses = [expected_status]
            if requires_auth:
                acceptable_statuses.extend([302, 401, 403])
            
            if response.status_code in acceptable_statuses:
                print(f"{GREEN}✓{RESET} {method} {path} [{response.status_code}] {description}")
                results['passed'].append((method, path, str(response.status_code)))
            elif response.status_code == 404:
                print(f"{RED}✗ 404{RESET} {method} {path} - Route not found {description}")
                results['failed'].append((method, path, "404 Not Found"))
            elif response.status_code in [301, 302, 303, 307, 308]:
                location = response.headers.get('Location', 'unknown')
                print(f"{YELLOW}⟳{RESET} {method} {path} [{response.status_code} → {location}] {description}")
                results['warnings'].append((method, path, f"Redirect to {location}"))
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

    print(f"\n{YELLOW}=== Health & Info Routes ==={RESET}")
    test_route("GET", "/health", 200, description="Health check")
    test_route("GET", "/health/live", 200, description="Liveness probe")
    test_route("GET", "/health/ready", 200, description="Readiness probe")
    test_route("GET", "/healthz", 200, description="Healthz probe")
    test_route("GET", "/api/version", 200, description="API version")

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

    print(f"\n{YELLOW}=== Auth Routes ==={RESET}")
    test_route("GET", "/login", 200, description="Login page")
    test_route("GET", "/signup", 200, description="Signup page")
    test_route("GET", "/get-started", 200, description="Get started")
    test_route("GET", "/logout", 302, description="Logout (expects redirect)")

    print(f"\n{YELLOW}=== Protected Routes (Dashboard & Main) ==={RESET}")
    test_route("GET", "/dashboard", 200, requires_auth=True, description="Dashboard")
    test_route("GET", "/calendar", 200, requires_auth=True, description="Calendar")
    test_route("GET", "/calendar_view", 200, requires_auth=True, description="Calendar view")
    test_route("GET", "/global_calendar", 200, requires_auth=True, description="Global calendar")
    test_route("GET", "/profile", 200, requires_auth=True, description="Profile")
    test_route("GET", "/home", 200, requires_auth=True, description="Home")

    print(f"\n{YELLOW}=== Trip Management Routes ==={RESET}")
    test_route("GET", "/bulk_add_trip", 200, requires_auth=True, description="Bulk add trip")
    test_route("GET", "/import_excel", 200, requires_auth=True, description="Import Excel")
    test_route("GET", "/what_if_scenario", 200, requires_auth=True, description="What-if scenario")
    test_route("GET", "/future_job_alerts", 200, requires_auth=True, description="Future job alerts")
    test_route("GET", "/export_future_alerts", 200, requires_auth=True, description="Export alerts")
    test_route("GET", "/export/trips/csv", 200, requires_auth=True, description="Export trips CSV")

    print(f"\n{YELLOW}=== Admin Routes ==={RESET}")
    test_route("GET", "/admin_settings", 200, requires_auth=True, description="Admin settings")
    test_route("GET", "/admin_privacy_tools", 200, requires_auth=True, description="Privacy tools (legacy)")
    test_route("GET", "/admin/privacy-tools", 200, requires_auth=True, description="Privacy tools")
    test_route("GET", "/admin/retention/expired", 200, requires_auth=True, description="Expired trips")
    test_route("GET", "/admin/audit-trail", 200, requires_auth=True, description="Audit trail")

    print(f"\n{YELLOW}=== API Routes - Employees ==={RESET}")
    test_route("GET", "/api/employees", 200, requires_auth=True, description="List employees")
    test_route("GET", "/api/employees/search", 200, requires_auth=True, description="Search employees")

    print(f"\n{YELLOW}=== API Routes - Trips ==={RESET}")
    test_route("GET", "/api/trips", 200, requires_auth=True, description="List trips")
    test_route("GET", "/api/calendar_data", 200, requires_auth=True, description="Calendar data")
    test_route("GET", "/api/test_calendar_data", 200, requires_auth=True, description="Test calendar data")

    print(f"\n{YELLOW}=== API Routes - Entry Requirements ==={RESET}")
    test_route("GET", "/api/entry-requirements", 200, description="Entry requirements API")

    print(f"\n{YELLOW}=== API Routes - Testing ==={RESET}")
    test_route("GET", "/api/test", 200, description="API test endpoint")
    test_route("GET", "/api/test_session", 200, description="Session test")

    print(f"\n{YELLOW}=== API Routes - Audit ==={RESET}")
    test_route("GET", "/api/audit-trail", 200, requires_auth=True, description="Audit trail API")
    test_route("GET", "/api/audit-trail/stats", 200, requires_auth=True, description="Audit stats")

    print(f"\n{YELLOW}=== API Routes - Retention/Privacy ==={RESET}")
    test_route("GET", "/api/retention/preview", 200, requires_auth=True, description="Retention preview")

    print(f"\n{YELLOW}=== Error Pages ==={RESET}")
    test_route("GET", "/this-route-does-not-exist-404", 404, description="404 error page")

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
    return results


if __name__ == "__main__":
    summary = run_all_routes()
    raise SystemExit(1 if summary['failed'] else 0)

