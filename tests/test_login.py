from __future__ import annotations

import json
from pathlib import Path

import pytest


FIXTURE_CREDENTIALS = Path(__file__).parent / "fixtures" / "credentials.json"


@pytest.fixture(scope="module")
def admin_credentials():
    with FIXTURE_CREDENTIALS.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    admin = payload["admin"]
    return admin["username"], admin["password"]


def test_login_page_renders(phase38_client):
    response = phase38_client.get("/login")
    assert response.status_code == 200
    assert b"Sign in to ComplyEur" in response.data or b"Login" in response.data


def test_login_succeeds_with_valid_credentials(phase38_client, admin_credentials):
    username, password = admin_credentials
    response = phase38_client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )

    assert response.status_code in (302, 303)
    assert "/dashboard" in response.headers.get("Location", "")

    with phase38_client.session_transaction() as session:
        assert session.get("user_id") == 1
        assert session.get("username") in (username, "admin")


def test_login_rejects_invalid_password(phase38_client, admin_credentials):
    username, _ = admin_credentials
    response = phase38_client.post(
        "/login",
        data={"username": username, "password": "wrong-password"},
        follow_redirects=False,
    )

    assert response.status_code == 200
    assert b"Invalid credentials" in response.data
