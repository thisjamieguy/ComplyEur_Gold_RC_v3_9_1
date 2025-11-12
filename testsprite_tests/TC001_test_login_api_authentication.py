import requests
from requests.exceptions import RequestException, Timeout

BASE_URL = "http://localhost:5001"
LOGIN_ENDPOINT = f"{BASE_URL}/login"
HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded"
}
TIMEOUT = 30

def test_login_api_authentication():
    session = requests.Session()

    try:
        # 1. Test successful login with valid credentials
        valid_credentials = {
            "username": "admin",
            "password": "correct_password"
        }
        response = session.post(
            LOGIN_ENDPOINT,
            data=valid_credentials,
            headers=HEADERS,
            timeout=TIMEOUT,
            allow_redirects=False
        )
        # Expecting a 200 status or a redirect (302) to dashboard on success.
        assert response.status_code in (200, 302), f"Expected 200 or 302, got {response.status_code}"
        # If redirected, location should be dashboard or similar
        if response.status_code == 302:
            location = response.headers.get("Location", "")
            assert "/dashboard" in location, f"Expected redirect to dashboard, got {location}"

        # 2. Test login failure with invalid credentials
        invalid_credentials = {
            "username": "admin",
            "password": "wrong_password"
        }
        response_fail = session.post(
            LOGIN_ENDPOINT,
            data=invalid_credentials,
            headers=HEADERS,
            timeout=TIMEOUT,
            allow_redirects=False
        )
        assert response_fail.status_code in (200, 401), f"Expected 401 or 200 for invalid credentials, got {response_fail.status_code}"
        # Check if response content indicates login failure when status is 200
        if response_fail.status_code == 200:
            content_lower = response_fail.text.lower()
            assert "invalid" in content_lower or "login" in content_lower, "Login failure not indicated in response content"

        # 3 & 4. Test rate limiting or CAPTCHA enforcement after multiple failed attempts
        # Assuming rate limiting or CAPTCHA triggered after several failed attempts
        limit_triggered = False
        max_attempts = 10
        for _ in range(max_attempts):
            resp = session.post(
                LOGIN_ENDPOINT,
                data=invalid_credentials,
                headers=HEADERS,
                timeout=TIMEOUT,
                allow_redirects=False
            )
            content_lower = resp.text.lower()
            if resp.status_code == 429 or "captcha" in content_lower:
                limit_triggered = True
                break
        assert limit_triggered, "Rate limiting or CAPTCHA not enforced or indicated after multiple failed attempts"

    except (RequestException, Timeout) as e:
        assert False, f"Request failed with exception: {e}"

test_login_api_authentication()
