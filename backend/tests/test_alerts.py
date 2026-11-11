"""Alert & Monitoring: cross-cutting live feed, stats, incidents, war-room wiring."""

from __future__ import annotations

SEVERITIES = {"info", "warning", "danger"}
CATEGORIES = {"risk", "customer", "inventory", "kpi", "goal", "delivery", "system"}


def test_overview_returns_a_live_feed(auth_client):
    resp = auth_client.get("/api/v1/alerts")
    assert resp.status_code == 200
    data = resp.json()
    assert data["alerts"]
    for a in data["alerts"]:
        assert a["title"] and a["detail"]
        assert a["severity"] in SEVERITIES
        assert a["category"] in CATEGORIES
        assert a["source"]
        assert a["status"] in {"open", "resolved"}


def test_feed_is_sorted_most_severe_first(auth_client):
    alerts = auth_client.get("/api/v1/alerts").json()["alerts"]
    rank = {"danger": 3, "warning": 2, "info": 1}
    ranks = [rank[a["severity"]] for a in alerts]
    assert ranks == sorted(ranks, reverse=True)


def test_feed_is_cross_cutting(auth_client):
    """The seeded org has a critical risk, churn, low stock, and a revenue dip —
    the feed should span multiple domains, not just one."""
    alerts = auth_client.get("/api/v1/alerts").json()["alerts"]
    categories = {a["category"] for a in alerts}
    assert {"risk", "customer", "inventory"} <= categories
    # The critical project risk surfaces as a danger-level alert.
    assert any(a["severity"] == "danger" for a in alerts)
    # Both derived (live) and persisted (system) alerts are present.
    assert any(a["derived"] for a in alerts)
    assert any(not a["derived"] for a in alerts)


def test_stats_and_incidents(auth_client):
    data = auth_client.get("/api/v1/alerts").json()
    stats = data["stats"]
    assert stats["total_open"] >= 1
    assert stats["critical"] >= 1
    assert stats["incidents_open"] >= 1
    assert stats["anomalies"] >= 1
    # One seeded incident is unresolved, one resolved.
    assert any(not i["resolved"] for i in data["incidents"])
    assert any(i["resolved"] for i in data["incidents"])


def test_war_room_surfaces_alerts(auth_client):
    events = auth_client.get("/api/v1/stratiqa-one/war-room").json()["business_events"]
    assert any(e["type"].startswith("alert_") for e in events)


def test_alerts_requires_auth(client):
    assert client.get("/api/v1/alerts").status_code in (401, 403)
