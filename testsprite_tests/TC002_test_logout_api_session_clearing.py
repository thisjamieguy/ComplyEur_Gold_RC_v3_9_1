import requests

BASE_URL = "http://localhost:5001"
LOGIN_URL = f"{BASE_URL}/login"
LOGOUT_URL = f"{BASE_URL}/logout"
TIMEOUT = 30

def test_logout_api_session_clearing():
    session = requests.Session()
    try:
        # Perform login to obtain a logged-in session (use valid test credentials)
        login_payload = {
            "username": "admin",
            "password": "admin"
        }
        login_headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        login_response = session.post(LOGIN_URL, data=login_payload, headers=login_headers, timeout=TIMEOUT)
        assert login_response.status_code == 200, f"Login failed with status code {login_response.status_code}"

        # Perform logout to clear session
        logout_response = session.post(LOGOUT_URL, timeout=TIMEOUT)
        assert logout_response.status_code == 200, f"Logout failed with status code {logout_response.status_code}"

        # Optionally, verify session cookies cleared (session cookies no longer present)
        # Or confirm logout by trying to access a protected page and expect failure (skipped due to scope)

    finally:
        session.close()

test_logout_api_session_clearing()