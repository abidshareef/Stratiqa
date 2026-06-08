"""Product Intelligence: catalog stats, stock status, demand, grounded signals."""

from __future__ import annotations

SEVERITIES = {"info", "warning", "danger", "success"}
STOCK = {"ok", "low", "out"}


def test_overview_returns_seeded_catalog(auth_client):
    resp = auth_client.get("/api/v1/products")
    assert resp.status_code == 200
    data = resp.json()
    assert data["stats"]["total_products"] >= 5
    assert len(data["products"]) == data["stats"]["total_products"]
    for p in data["products"]:
        assert p["product_name"]
        assert p["stock_status"] in STOCK


def test_catalog_ordered_by_revenue(auth_client):
    products = auth_client.get("/api/v1/products").json()["products"]
    revenues = [p["revenue"] or 0 for p in products]
    assert revenues == sorted(revenues, reverse=True)


def test_low_stock_is_flagged(auth_client):
    data = auth_client.get("/api/v1/products").json()
    # Seed has two SKUs at/below reorder level.
    assert data["stats"]["low_stock_count"] >= 2
    low = [p for p in data["products"] if p["stock_status"] in {"low", "out"}]
    assert len(low) == data["stats"]["low_stock_count"]
    for p in low:
        assert p["quantity"] <= p["reorder_level"]


def test_signals_are_explainable_and_flag_stockouts(auth_client):
    signals = auth_client.get("/api/v1/products").json()["signals"]
    assert signals
    for s in signals:
        assert s["title"] and s["finding"]
        assert s["severity"] in SEVERITIES
        assert 0 <= s["confidence_score"] <= 100
        assert s["data_sources"]
    assert any("reorder level" in s["title"] for s in signals)


def test_top_product_present(auth_client):
    stats = auth_client.get("/api/v1/products").json()["stats"]
    assert stats["top_product"]
    assert stats["total_revenue"] > 0


def test_products_requires_auth(client):
    assert client.get("/api/v1/products").status_code in (401, 403)
