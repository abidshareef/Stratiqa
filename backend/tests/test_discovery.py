"""Business Discovery: founder interview -> DNA + blueprint + grounded goals.

Asserts the onboarding journey makes a brand-new organization non-empty using
only the founder's own inputs (no generic/fabricated data).
"""

from __future__ import annotations

import uuid

INTERVIEW = {
    "industry": "SaaS",
    "business_model": "Subscription",
    "company_size": "11-50",
    "annual_revenue": 1_500_000,
    "employee_count": 22,
    "primary_goals": ["Reach $2M ARR", "Launch self-serve onboarding"],
    "main_challenges": ["High churn", "Long sales cycle"],
    "target_market": "B2B mid-market",
}


def _new_org_headers(client) -> dict:
    email = f"disc-{uuid.uuid4().hex[:8]}@example.com"
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "full_name": "Disco Founder",
            "organization_name": "Discovery Co",
        },
    ).json()
    return {"Authorization": f"Bearer {reg['tokens']['access_token']}"}


def test_blueprint_absent_before_discovery(client):
    headers = _new_org_headers(client)
    assert client.get("/api/v1/discovery/blueprint", headers=headers).status_code == 404


def test_run_discovery_returns_profile_dna_blueprint(client):
    headers = _new_org_headers(client)
    resp = client.post("/api/v1/discovery/run", json=INTERVIEW, headers=headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["profile"]["industry"] == "SaaS"
    # 1.5M revenue -> "growth"; subscription/22 emp -> low complexity; B2B market.
    assert body["dna"]["growth_stage"] == "growth"
    assert body["dna"]["market_type"] == "B2B"
    bp = body["blueprint"]["blueprint_json"]
    assert bp["stated_goals"] == INTERVIEW["primary_goals"]
    assert len(bp["recommended_focus_areas"]) >= 1
    assert len(bp["suggested_kpis"]) >= 1


def test_discovery_seeds_grounded_goals(client):
    headers = _new_org_headers(client)
    assert client.get("/api/v1/goals", headers=headers).json() == []  # empty before

    client.post("/api/v1/discovery/run", json=INTERVIEW, headers=headers)

    goals = client.get("/api/v1/goals", headers=headers).json()
    titles = {g["title"] for g in goals}
    assert titles == set(INTERVIEW["primary_goals"])
    # goal_type is classified transparently from the goal text.
    by_title = {g["title"]: g for g in goals}
    assert by_title["Reach $2M ARR"]["goal_type"] == "revenue"
    assert by_title["Launch self-serve onboarding"]["goal_type"] in {
        "expansion",
        "product",
    }


def test_discovery_is_idempotent(client):
    headers = _new_org_headers(client)
    client.post("/api/v1/discovery/run", json=INTERVIEW, headers=headers)
    client.post("/api/v1/discovery/run", json=INTERVIEW, headers=headers)
    goals = client.get("/api/v1/goals", headers=headers).json()
    # Re-running must not duplicate the same goals.
    assert len(goals) == len(INTERVIEW["primary_goals"])


def test_dashboard_non_empty_after_discovery(client):
    headers = _new_org_headers(client)
    client.post("/api/v1/discovery/run", json=INTERVIEW, headers=headers)
    home = client.get("/api/v1/stratiqa-one/home", headers=headers).json()
    assert len(home["goals"]) == len(INTERVIEW["primary_goals"])


def test_seeded_demo_org_has_blueprint(auth_client):
    """The demo org's seed runs discovery, so its Business DNA is available."""
    resp = auth_client.get("/api/v1/discovery/blueprint")
    assert resp.status_code == 200
    assert resp.json()["blueprint_json"]["industry"] == "Manufacturing"

    dna = auth_client.get("/api/v1/discovery/dna")
    assert dna.status_code == 200
    assert dna.json()["operational_complexity"] == "high"
