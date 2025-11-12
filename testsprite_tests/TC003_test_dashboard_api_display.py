import requests

BASE_URL = "http://localhost:5001"
TIMEOUT = 30

def test_dashboard_api_display():
    url = f"{BASE_URL}/dashboard"
    headers = {
        "Accept": "text/html"
    }
    try:
        response = requests.get(url, headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as e:
        assert False, f"Request to {url} failed: {e}"

    # Validate status code
    assert response.status_code == 200, f"Expected status code 200 but got {response.status_code}"

    # Validate that content type is HTML
    content_type = response.headers.get('Content-Type', '')
    assert 'text/html' in content_type, f"Expected 'text/html' in Content-Type header but got {content_type}"

test_dashboard_api_display()