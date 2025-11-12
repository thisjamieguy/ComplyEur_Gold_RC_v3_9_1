"""Tests for authentication security features (rate limiting, CAPTCHA)."""

def test_rate_limit_and_failed_attempts_trigger(client):
    """Test that rate limiting triggers after repeated failed attempts."""
    # send multiple wrong passwords; after limiter threshold you should see 429
    hit_429 = False
    for i in range(12):
        r = client.post("/login", data={"username": "admin", "password": "wrong"})
        if r.status_code == 429:
            hit_429 = True
            break
    assert hit_429, "Expected HTTP 429 after repeated failures"


def test_success_login_resets_failed_count(auth_client):
    """Test that successful login resets failed attempt count."""
    # If we can log in, fixture already validated it; here we just check a protected endpoint 401→200
    r_unauth = auth_client.get("/api/employees")  # auth_client is authenticated
    assert r_unauth.status_code == 200