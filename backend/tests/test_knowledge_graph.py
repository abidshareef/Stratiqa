"""Knowledge Graph: materialized entity/relationship graph from real data."""

from __future__ import annotations

import uuid


def test_graph_builds_for_demo_org(auth_client):
    resp = auth_client.get("/api/v1/knowledge-graph")
    assert resp.status_code == 200
    graph = resp.json()
    assert len(graph["nodes"]) >= 5
    cats = {n["category"] for n in graph["nodes"]}
    assert "organization" in cats
    assert {"goal", "project"} & cats

    # Every edge must connect two real nodes (no dangling references).
    node_ids = {n["id"] for n in graph["nodes"]}
    assert graph["edges"]
    for e in graph["edges"]:
        assert e["source"] in node_ids and e["target"] in node_ids

    # Recommendations are grounded cross-links to the projects they cite.
    assert any(e["type"] == "addresses" for e in graph["edges"])
    assert graph["stats"]["organization"] == 1


def test_graph_rebuild_is_stable(auth_client):
    first = auth_client.post("/api/v1/knowledge-graph/rebuild").json()
    second = auth_client.post("/api/v1/knowledge-graph/rebuild").json()
    # Rebuilding from unchanged data yields the same node/edge counts (no growth).
    assert len(first["nodes"]) == len(second["nodes"])
    assert len(first["edges"]) == len(second["edges"])


def test_graph_for_new_org_after_discovery(client):
    email = f"kg-{uuid.uuid4().hex[:8]}@example.com"
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "full_name": "KG",
            "organization_name": "Graph Co",
        },
    ).json()
    headers = {"Authorization": f"Bearer {reg['tokens']['access_token']}"}
    client.post(
        "/api/v1/discovery/run",
        json={
            "industry": "SaaS",
            "business_model": "Subscription",
            "company_size": "11-50",
            "annual_revenue": 1_200_000,
            "employee_count": 20,
            "primary_goals": ["Reach $2M ARR"],
            "main_challenges": ["Churn"],
            "target_market": "B2B",
        },
        headers=headers,
    )
    graph = client.get("/api/v1/knowledge-graph", headers=headers).json()
    cats = {n["category"] for n in graph["nodes"]}
    assert "organization" in cats and "goal" in cats
