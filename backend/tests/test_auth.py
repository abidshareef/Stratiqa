"""Authentication, token issuance, and access control."""

from __future__ import annotations

import uuid

from tests.conftest import DEMO_EMAIL, DEMO_PASSWORD


def test_login_success_returns_token_pair(client):
    resp = client.post(
        "/api/v1/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["organization"]["name"] == "Northwind Robotics"
    assert body["tokens"]["access_token"]
    assert body["tokens"]["refresh_token"]
    assert body["tokens"]["token_type"] == "bearer"


def test_login_wrong_password_rejected(client):
    resp = client.post(
        "/api/v1/auth/login", json={"email": DEMO_EMAIL, "password": "wrong-password"}
    )
    assert resp.status_code in (400, 401)


def test_protected_route_requires_auth(client):
    assert client.get("/api/v1/stratiqa-one/home").status_code in (401, 403)


def test_me_returns_current_user(auth_client):
    resp = auth_client.get("/api/v1/auth/me")
    assert resp.status_code == 200
    assert resp.json()["email"] == DEMO_EMAIL


def test_refresh_rotates_access_token(client):
    login = client.post(
        "/api/v1/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD}
    ).json()
    refresh = login["tokens"]["refresh_token"]
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert resp.status_code == 200
    assert resp.json()["access_token"]


def test_register_creates_org_and_auto_logs_in(client):
    email = f"new-{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "full_name": "New Founder",
            "organization_name": "Fresh Ventures",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["organization"]["name"] == "Fresh Ventures"
    assert body["tokens"]["access_token"]


def test_new_org_is_data_isolated(client):
    """A brand-new org must not see the seeded demo org's goals/recommendations."""
    email = f"iso-{uuid.uuid4().hex[:8]}@example.com"
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "full_name": "Iso",
            "organization_name": "Isolated Co",
        },
    ).json()
    token = reg["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    goals = client.get("/api/v1/goals", headers=headers)
    recs = client.get("/api/v1/recommendations", headers=headers)
    assert goals.status_code == 200 and goals.json() == []
    assert recs.status_code == 200 and recs.json() == []
