"""System / health endpoints."""

from __future__ import annotations


def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"] == "STRATIQA"


def test_root_metadata(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["api_prefix"] == "/api/v1"
