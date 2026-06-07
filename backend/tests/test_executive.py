"""Executive surfaces: STRATIQA One Home, War Room, Ask, analytics, twin,
recommendations, goals, projects, briefs, reports.

These assert not just 200s but that the responses are *grounded* in the seeded
data (the product principle: intelligence before analytics, never generic).
"""

from __future__ import annotations


def test_home_is_grounded(auth_client):
    resp = auth_client.get("/api/v1/stratiqa-one/home")
    assert resp.status_code == 200
    home = resp.json()
    for key in (
        "welcome",
        "summary",
        "todays_priorities",
        "risks",
        "opportunities",
        "goals",
        "projects",
        "recommendations",
    ):
        assert key in home
    # Seeded org has active goals + grounded recommendations.
    assert len(home["goals"]) >= 1
    assert len(home["recommendations"]) >= 1


def test_war_room(auth_client):
    resp = auth_client.get("/api/v1/stratiqa-one/war-room")
    assert resp.status_code == 200
    war = resp.json()
    assert "critical_risks" in war and "twin_insights" in war


def test_ask_returns_explainable_answer(auth_client):
    resp = auth_client.post(
        "/api/v1/stratiqa-one/ask",
        json={"query": "How are we tracking to our revenue goal?"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"]
    assert 0 <= body["confidence_score"] <= 100
    assert isinstance(body["data_sources"], list)


def test_recommendations_have_explainability_fields(auth_client):
    resp = auth_client.get("/api/v1/recommendations")
    assert resp.status_code == 200
    recs = resp.json()
    assert len(recs) >= 1
    for rec in recs:
        # Every recommendation must carry the explainability contract.
        assert rec["title"]
        assert rec["reasoning"]
        assert rec["expected_impact"]
        assert 0 <= rec["confidence_score"] <= 100
        assert rec["risk_level"] in {"low", "medium", "high", "critical"}
        assert rec["data_sources"]


def test_recommendation_accept_changes_status(auth_client):
    rec_id = auth_client.get("/api/v1/recommendations").json()[0]["id"]
    resp = auth_client.post(f"/api/v1/recommendations/{rec_id}/accept")
    assert resp.status_code == 200
    assert resp.json()["status"] == "accepted"


def test_recommendations_refresh_is_idempotent(auth_client):
    first = auth_client.post("/api/v1/recommendations/refresh")
    second = auth_client.post("/api/v1/recommendations/refresh")
    assert first.status_code == 200 and second.status_code == 200
    # Refreshing the same unchanged data should not multiply recommendations.
    assert len(second.json()) == len(first.json())


def test_goals_list_and_detail_forecast(auth_client):
    goals = auth_client.get("/api/v1/goals").json()
    assert len(goals) >= 1
    detail = auth_client.get(f"/api/v1/goals/{goals[0]['id']}")
    assert detail.status_code == 200
    body = detail.json()
    assert "completion_forecast" in body
    assert "risk_indicator" in body


def test_create_goal(auth_client):
    resp = auth_client.post(
        "/api/v1/goals",
        json={
            "title": "Hit 99.9% uptime",
            "goal_type": "operational",
            "target_value": 99.9,
        },
    )
    assert resp.status_code == 201
    assert resp.json()["title"] == "Hit 99.9% uptime"


def test_projects_list(auth_client):
    resp = auth_client.get("/api/v1/projects")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_analytics_overview(auth_client):
    resp = auth_client.get("/api/v1/analytics/overview")
    assert resp.status_code == 200
    body = resp.json()
    for key in ("kpis", "revenue_trend", "goal_progress", "project_health"):
        assert key in body
    assert len(body["kpis"]) >= 1


def test_twin_simulation_produces_outcome(auth_client):
    resp = auth_client.post(
        "/api/v1/twin/simulate",
        json={"scenario_name": "Scale hiring", "hiring_change": 25.0},
    )
    assert resp.status_code == 200
    outcome = resp.json()["outcome"]
    assert "narrative" in outcome
    assert 0 <= outcome["confidence_score"] <= 100


def test_brief_generation(auth_client):
    resp = auth_client.post("/api/v1/briefs/generate", params={"brief_type": "morning"})
    assert resp.status_code == 201
    assert resp.json()["brief_type"] == "morning"
    assert resp.json()["content"]


def test_brief_invalid_type_rejected(auth_client):
    resp = auth_client.post("/api/v1/briefs/generate", params={"brief_type": "hourly"})
    assert resp.status_code == 400


def test_report_generation(auth_client):
    resp = auth_client.post(
        "/api/v1/reports/generate", params={"report_type": "executive"}
    )
    assert resp.status_code == 201
    assert resp.json()["report_type"] == "executive"
