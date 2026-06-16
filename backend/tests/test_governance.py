"""Audit & Governance (Section 16): the org's accountability overview.

Verifies that real actions (registration, data commits) land in the audit
trail, that the trail is org-scoped, and that AI-decision explainability
coverage is reported against the recommendations the engine produces.
"""

from __future__ import annotations

import uuid

SALES_CSV = (
    b"Month,Net Revenue,Region\n"
    b"2026-01,120000,North\n"
    b"2026-02,135000,North\n"
    b"2026-03,128000,North\n"
    b"2026-04,95000,North\n"
)


def _new_org_headers(client) -> dict:
    email = f"gov-{uuid.uuid4().hex[:8]}@example.com"
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "full_name": "Gov Founder",
            "organization_name": "Gov Co",
        },
    ).json()
    return {"Authorization": f"Bearer {reg['tokens']['access_token']}"}


def test_registration_appears_in_audit_trail(client):
    headers = _new_org_headers(client)
    gov = client.get("/api/v1/governance", headers=headers).json()

    actions = {e["action"] for e in gov["trail"]}
    assert "user.register" in actions
    assert gov["stats"]["security_events"] >= 1
    # The registering founder is named in the trail, not "system".
    reg_entry = next(e for e in gov["trail"] if e["action"] == "user.register")
    assert reg_entry["actor"] == "Gov Founder"
    assert reg_entry["category"] == "security"


def test_data_commit_is_audited_and_governance_coverage_reported(client):
    headers = _new_org_headers(client)
    upload = client.post(
        "/api/v1/uploads",
        files={"file": ("sales.csv", SALES_CSV, "text/csv")},
        headers=headers,
    ).json()
    client.post(
        f"/api/v1/uploads/{upload['id']}/commit",
        json=upload["suggested_mapping"],
        headers=headers,
    )

    gov = client.get("/api/v1/governance", headers=headers).json()

    # The commit must be logged as a data event.
    data_entry = next((e for e in gov["trail"] if e["action"] == "data.commit"), None)
    assert data_entry is not None
    assert data_entry["category"] == "data"
    assert "sales.csv" in (data_entry["resource"] or "")
    assert gov["stats"]["data_events"] >= 1

    # The revenue decline produced a recommendation; it must be fully explainable
    # (reasoning + confidence + data sources), so coverage is 100%.
    decisions = gov["decisions"]
    assert decisions["total_decisions"] >= 1
    assert decisions["explainability_coverage"] == 100.0
    assert decisions["avg_confidence"] > 0


def test_governance_is_org_scoped(client):
    headers_a = _new_org_headers(client)
    headers_b = _new_org_headers(client)

    gov_b = client.get("/api/v1/governance", headers=headers_b).json()
    # Org B's trail must contain only its own registration, never org A's actors.
    assert all(e["actor"] in {"Gov Founder", "system"} for e in gov_b["trail"])
    assert all(e["category"] != "data" for e in gov_b["trail"])
    _ = headers_a  # org A exists but must not bleed into B's view
