"""Tests for health endpoints."""

def test_health_endpoints(client):
    """Test all health endpoints return consistent JSON."""
    for path in ["/health", "/health/live", "/health/ready", "/healthz"]:
        r = client.get(path)
        j = r.get_json()
        assert r.status_code == 200
        assert j.get("status") == "healthy"
        assert "version" in j
    
    vr = client.get("/api/version")
    assert vr.status_code == 200
    assert "version" in vr.get_json()
