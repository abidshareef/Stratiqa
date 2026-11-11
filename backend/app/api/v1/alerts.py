"""Alert & Monitoring endpoints — a cross-cutting live alert feed + incidents."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.deps import CurrentOrgId, DbDep
from app.schemas.monitoring import MonitoringOverview
from app.services import monitoring

router = APIRouter(prefix="/alerts", tags=["alerts-monitoring"])


@router.get("", response_model=MonitoringOverview)
def alerts_overview(db: DbDep, org_id: CurrentOrgId):
    return monitoring.overview(db, org_id)
