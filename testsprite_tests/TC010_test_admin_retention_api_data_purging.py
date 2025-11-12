import requests

BASE_URL = "http://localhost:5001"
TIMEOUT = 30

HEADERS = {
    'Accept': 'application/json'
}


def test_admin_retention_api_data_purging():
    # Preview expired trips
    preview_url = f"{BASE_URL}/api/retention/preview"
    try:
        preview_response = requests.get(preview_url, headers=HEADERS, timeout=TIMEOUT)
        preview_response.raise_for_status()
        preview_data = preview_response.json()
        assert isinstance(preview_data, dict), "Preview response is not a JSON object"
        assert "expired_trips" in preview_data, "'expired_trips' key missing in preview response"
        expired_trips = preview_data["expired_trips"]
        assert isinstance(expired_trips, list), "'expired_trips' is not a list"
    except requests.RequestException as e:
        assert False, f"Preview expired trips request failed: {str(e)}"

    # List expired trips page
    list_url = f"{BASE_URL}/admin/retention/expired"
    try:
        list_response = requests.get(list_url, headers=HEADERS, timeout=TIMEOUT)
        assert list_response.status_code == 200, f"Expired trips listing failed with status {list_response.status_code}"
        # Content can be HTML page, so no JSON assertion here. Just check content existence.
        assert list_response.content, "Expired trips list response has no content"
    except requests.RequestException as e:
        assert False, f"List expired trips request failed: {str(e)}"

    # Purge expired trips
    purge_url = f"{BASE_URL}/admin/retention/purge"
    try:
        purge_response = requests.post(purge_url, headers=HEADERS, timeout=TIMEOUT)
        purge_response.raise_for_status()
        # Purge API returns a 200 status and confirmation text presumably
        assert "purged" in purge_response.text.lower(), "Purge confirmation not found in response"
    except requests.RequestException as e:
        assert False, f"Purge expired trips request failed: {str(e)}"


test_admin_retention_api_data_purging()
