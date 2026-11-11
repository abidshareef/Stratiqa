"""Audit & Governance endpoints (Section 16) — the org's accountability view:
an audit trail plus AI-decision explainability coverage."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.deps import CurrentOrgId, DbDep
from app.schemas.governance import GovernanceOverview
from app.services import governance

router = APIRouter(prefix="/governance", tags=["audit-governance"])


@router.get("", response_model=GovernanceOverview)
def governance_overview(db: DbDep, org_id: CurrentOrgId):
    return governance.overview(db, org_id)
