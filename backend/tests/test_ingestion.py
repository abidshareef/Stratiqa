"""Data ingestion: upload a business file -> map columns -> entities + insights.

Asserts that a brand-new org can feed real data via file upload (not just the
short founder interview) and that committed data immediately drives the
recommendation engine.
"""

from __future__ import annotations

import uuid

# A monthly sales report with a sharp decline in the final month (128k -> 95k).
SALES_CSV = (
    b"Month,Net Revenue,Region\n"
    b"2026-01,120000,North\n"
    b"2026-02,135000,North\n"
    b"2026-03,128000,North\n"
    b"2026-04,95000,North\n"
)


def _new_org_headers(client) -> dict:
    email = f"ingest-{uuid.uuid4().hex[:8]}@example.com"
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "full_name": "Ingest Founder",
            "organization_name": "Ingest Co",
        },
    ).json()
    return {"Authorization": f"Bearer {reg['tokens']['access_token']}"}


def _upload(client, headers, name, data, content_type):
    return client.post(
        "/api/v1/uploads",
        files={"file": (name, data, content_type)},
        headers=headers,
    )


def test_csv_upload_parses_and_suggests_mapping(client):
    headers = _new_org_headers(client)
    resp = _upload(client, headers, "sales.csv", SALES_CSV, "text/csv")
    assert resp.status_code == 201
    body = resp.json()
    assert body["file_kind"] == "csv"
    assert body["status"] == "parsed"
    assert body["row_count"] == 4
    assert body["columns"] == ["Month", "Net Revenue", "Region"]
    # Auto-suggestion should route a revenue column to a KPI import.
    sm = body["suggested_mapping"]
    assert sm["target"] == "kpi"
    assert sm["fields"]["value"] == "Net Revenue"
    assert sm["fields"]["date"] == "Month"


def test_commit_creates_kpis_and_refreshes_recommendations(client):
    headers = _new_org_headers(client)
    upload = _upload(client, headers, "sales.csv", SALES_CSV, "text/csv").json()

    commit = client.post(
        f"/api/v1/uploads/{upload['id']}/commit",
        json=upload["suggested_mapping"],
        headers=headers,
    )
    assert commit.status_code == 200
    result = commit.json()
    assert result["created"]["kpis"] == 4
    assert result["skipped"] == 0
    assert result["total"] == 4

    # The 26% month-over-month drop must surface as a grounded recommendation.
    recs = client.get("/api/v1/recommendations", headers=headers).json()
    assert any("Net Revenue" in r["title"] and "decline" in r["title"].lower() for r in recs)

    # The commit must report the analysis shift the new data caused, so the user
    # recognizes *what* changed — not just that a refresh happened.
    changes = result["analysis_changes"]
    assert any("Net Revenue" in t and "decline" in t.lower() for t in changes["new_insights"])
    assert changes["resolved_insights"] == []


def test_commit_reports_resolved_insight_when_data_recovers(client):
    """A second, healthier upload should *resolve* the prior decline signal."""
    headers = _new_org_headers(client)

    decline = _upload(client, headers, "q1.csv", SALES_CSV, "text/csv").json()
    first = client.post(
        f"/api/v1/uploads/{decline['id']}/commit",
        json=decline["suggested_mapping"],
        headers=headers,
    ).json()
    assert first["analysis_changes"]["new_insights"]  # decline flagged

    # New month recovers above the previous reading; the latest-vs-previous
    # comparison no longer trips the 10% decline threshold.
    recover_csv = b"Month,Net Revenue,Region\n2026-05,150000,North\n"
    recover = _upload(client, headers, "may.csv", recover_csv, "text/csv").json()
    second = client.post(
        f"/api/v1/uploads/{recover['id']}/commit",
        json=recover["suggested_mapping"],
        headers=headers,
    ).json()
    resolved = second["analysis_changes"]["resolved_insights"]
    assert any("Net Revenue" in t and "decline" in t.lower() for t in resolved)


def test_products_upload_commit(client):
    headers = _new_org_headers(client)
    csv = b"Product,Category,Revenue,Units\nWidget,Hardware,50000,200\nGadget,Hardware,30000,150\n"
    upload = _upload(client, headers, "products.csv", csv, "text/csv").json()
    assert upload["suggested_mapping"]["target"] == "products"

    commit = client.post(
        f"/api/v1/uploads/{upload['id']}/commit",
        json=upload["suggested_mapping"],
        headers=headers,
    ).json()
    assert commit["created"]["products"] == 2

    products = client.get("/api/v1/products", headers=headers).json()
    assert products["stats"]["total_products"] >= 2


def test_image_upload_marked_manual_required(client):
    headers = _new_org_headers(client)
    resp = _upload(client, headers, "chart.png", b"\x89PNG\r\n\x1a\n fake", "image/png")
    assert resp.status_code == 201
    body = resp.json()
    assert body["file_kind"] == "image"
    assert body["status"] == "manual_required"
    assert body["columns"] == []


def test_commit_requires_mapped_required_field(client):
    headers = _new_org_headers(client)
    upload = _upload(client, headers, "sales.csv", SALES_CSV, "text/csv").json()
    # Customers target needs a customer_name column we didn't map.
    resp = client.post(
        f"/api/v1/uploads/{upload['id']}/commit",
        json={"target": "customers", "fields": {}},
        headers=headers,
    )
    assert resp.status_code == 400


def test_uploads_are_org_scoped(client):
    headers_a = _new_org_headers(client)
    headers_b = _new_org_headers(client)
    upload = _upload(client, headers_a, "sales.csv", SALES_CSV, "text/csv").json()
    # Org B must not see or fetch org A's upload.
    assert client.get(f"/api/v1/uploads/{upload['id']}", headers=headers_b).status_code == 404
    assert client.get("/api/v1/uploads", headers=headers_b).json() == []
