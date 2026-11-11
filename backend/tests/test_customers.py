"""Customer Intelligence: overview stats, per-account health, grounded signals."""

from __future__ import annotations

SEVERITIES = {"info", "warning", "danger", "success"}
STATUSES = {"healthy", "watch", "at_risk"}


def test_overview_returns_seeded_customer_base(auth_client):
    resp = auth_client.get("/api/v1/customers")
    assert resp.status_code == 200
    data = resp.json()
    assert data["stats"]["total_customers"] >= 6
    assert len(data["customers"]) == data["stats"]["total_customers"]
    for c in data["customers"]:
        assert c["customer_name"]
        assert c["status"] in STATUSES


def test_accounts_are_ordered_by_churn_risk(auth_client):
    customers = auth_client.get("/api/v1/customers").json()["customers"]
    risks = [c["churn_risk"] or 0 for c in customers]
    assert risks == sorted(risks, reverse=True)


def test_at_risk_accounts_are_flagged(auth_client):
    data = auth_client.get("/api/v1/customers").json()
    # Seed includes two accounts with churn risk >= 60.
    assert data["stats"]["at_risk_count"] >= 2
    at_risk = [c for c in data["customers"] if c["status"] == "at_risk"]
    assert len(at_risk) == data["stats"]["at_risk_count"]
    for c in at_risk:
        assert c["churn_risk"] >= 60


def test_signals_are_explainable_and_flag_churn(auth_client):
    data = auth_client.get("/api/v1/customers").json()
    signals = data["signals"]
    assert signals
    for s in signals:
        assert s["title"] and s["finding"]
        assert s["severity"] in SEVERITIES
        assert 0 <= s["confidence_score"] <= 100
        assert s["data_sources"]
    # The churn signal should be present and elevated.
    assert any("churn risk" in s["title"] and s["severity"] in {"warning", "danger"}
               for s in signals)


def test_customers_requires_auth(client):
    assert client.get("/api/v1/customers").status_code in (401, 403)
