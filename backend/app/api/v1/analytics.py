"""Analytics endpoints — quantitative layer for the executive dashboard."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.deps import CurrentOrgId, DbDep
from app.schemas.analytics import AnalyticsOverview
from app.services import analytics

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
def overview(db: DbDep, org_id: CurrentOrgId):
    return analytics.overview(db, org_id)
