"""Tests for /api/employees endpoints."""

def test_employee_crud_list_create(auth_client):
    """Test employee list and create operations."""
    # list (empty)
    r = auth_client.get("/api/employees")
    assert r.status_code == 200
    assert isinstance(r.get_json(), list)
    
    # create
    r = auth_client.post("/api/employees", json={"name": "Alice"})
    assert r.status_code == 201
    eid = r.get_json()["id"]
    assert isinstance(eid, int)
    
    # list (has Alice)
    r = auth_client.get("/api/employees")
    names = [e["name"] for e in r.get_json()]
    assert "Alice" in names
