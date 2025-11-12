import requests

BASE_URL = "http://localhost:5001"
TIMEOUT = 30

def test_health_check_api_endpoints():
    endpoints = {
        "health": "/health",
        "readiness": "/health/ready",
        "liveness": "/health/live",
        "simple_health": "/healthz",
        "version": "/api/version"
    }
    try:
        # Test /health endpoint
        resp = requests.get(f"{BASE_URL}{endpoints['health']}", timeout=TIMEOUT)
        assert resp.status_code in (200, 503)
        if resp.status_code == 200:
            json_data = resp.json()
            assert "status" in json_data and isinstance(json_data["status"], str)
            assert "timestamp" in json_data and isinstance(json_data["timestamp"], str)
            assert "service" in json_data and isinstance(json_data["service"], str)

        # Test /health/ready endpoint
        resp = requests.get(f"{BASE_URL}{endpoints['readiness']}", timeout=TIMEOUT)
        assert resp.status_code in (200, 503)

        # Test /health/live endpoint
        resp = requests.get(f"{BASE_URL}{endpoints['liveness']}", timeout=TIMEOUT)
        assert resp.status_code == 200

        # Test /healthz endpoint
        resp = requests.get(f"{BASE_URL}{endpoints['simple_health']}", timeout=TIMEOUT)
        assert resp.status_code == 200
        assert resp.text.strip() == "OK"

        # Test /api/version endpoint
        resp = requests.get(f"{BASE_URL}{endpoints['version']}", timeout=TIMEOUT)
        assert resp.status_code == 200
        json_data = resp.json()
        assert "version" in json_data and isinstance(json_data["version"], str)

    except requests.RequestException as e:
        assert False, f"Request failed: {e}"

test_health_check_api_endpoints()
