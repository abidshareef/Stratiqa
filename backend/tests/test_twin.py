"""Business Twin: grounded simulation + data-anchored twin insights."""

from __future__ import annotations


def test_simulation_outcome_is_directionally_sane(auth_client):
    resp = auth_client.post(
        "/api/v1/twin/simulate",
        json={
            "scenario_name": "Cut marketing, hold price",
            "marketing_spend_change": -20.0,
        },
    )
    assert resp.status_code == 200
    outcome = resp.json()["outcome"]
    # Cutting marketing should not project a revenue increase.
    assert outcome["revenue_impact"] <= 0
    assert outcome["narrative"]


def test_simulation_is_persisted_and_listed(auth_client):
    before = len(auth_client.get("/api/v1/twin/simulations").json())
    auth_client.post(
        "/api/v1/twin/simulate",
        json={"scenario_name": "Expansion bet", "market_expansion": 30.0},
    )
    after = auth_client.get("/api/v1/twin/simulations").json()
    assert len(after) == before + 1


def test_war_room_twin_insights_are_grounded(auth_client):
    war = auth_client.get("/api/v1/stratiqa-one/war-room").json()
    insights = war["twin_insights"]
    assert insights
    # Demo org has revenue KPIs + a risk profile, so insights reference them.
    joined = " ".join(insights).lower()
    assert "revenue" in joined or "risk" in joined
