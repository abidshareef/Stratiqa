"""AI Agent layer: specialist roster, grounded insights, and Q&A."""

from __future__ import annotations

ALL_AGENTS = {
    "STRATIQA_ONE",
    "FINANCE",
    "SALES",
    "PROJECT",
    "RISK",
    "CUSTOMER_SUCCESS",
    "PRODUCT",
    "HR",
}
SEVERITIES = {"info", "warning", "danger", "success"}


def test_roster_lists_all_specialist_agents(auth_client):
    resp = auth_client.get("/api/v1/agents")
    assert resp.status_code == 200
    agents = resp.json()["agents"]
    assert {a["agent_type"] for a in agents} == ALL_AGENTS
    for a in agents:
        assert a["name"] and a["domain"]
        assert a["headline"]
        assert a["top_severity"] in SEVERITIES


def test_finance_agent_insights_are_explainable(auth_client):
    resp = auth_client.get("/api/v1/agents/finance")
    assert resp.status_code == 200
    detail = resp.json()
    assert detail["agent_type"] == "FINANCE"
    assert detail["insights"]
    for ins in detail["insights"]:
        assert ins["title"] and ins["finding"]
        assert ins["severity"] in SEVERITIES
        assert 0 <= ins["confidence_score"] <= 100
        assert ins["data_sources"]


def test_risk_agent_flags_the_seeded_critical_risk(auth_client):
    detail = auth_client.get("/api/v1/agents/risk").json()
    sev = {i["severity"] for i in detail["insights"]}
    assert "danger" in sev  # demo org has a critical, unmitigated risk


def test_unknown_agent_returns_404(auth_client):
    assert auth_client.get("/api/v1/agents/wizard").status_code == 404
    assert (
        auth_client.post("/api/v1/agents/wizard/ask", json={"query": "hi"}).status_code
        == 404
    )


def test_agent_ask_returns_grounded_answer(auth_client):
    resp = auth_client.post(
        "/api/v1/agents/finance/ask",
        json={"query": "How is our financial health?"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["agent_type"] == "FINANCE"
    assert body["answer"]
    assert 0 <= body["confidence_score"] <= 100
    assert body["insights"]


def test_agent_type_is_case_insensitive(auth_client):
    assert auth_client.get("/api/v1/agents/Finance").status_code == 200
    assert auth_client.get("/api/v1/agents/STRATIQA_ONE").status_code == 200
