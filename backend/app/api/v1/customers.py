"""Customer Intelligence endpoints — health, churn, support, grounded signals."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.deps import CurrentOrgId, DbDep
from app.schemas.customers import CustomerOverview
from app.services import customer_intelligence

router = APIRouter(prefix="/customers", tags=["customer-intelligence"])


@router.get("", response_model=CustomerOverview)
def customer_overview(db: DbDep, org_id: CurrentOrgId):
    return customer_intelligence.overview(db, org_id)
