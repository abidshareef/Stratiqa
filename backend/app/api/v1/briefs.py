"""Executive brief endpoints — morning/evening/weekly/monthly."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.deps import CurrentOrgId, DbDep
from app.models.reporting import ExecutiveBrief
from app.schemas.report import BriefOut
from app.services import brief_generator

router = APIRouter(prefix="/briefs", tags=["briefs"])


@router.get("", response_model=list[BriefOut])
def list_briefs(db: DbDep, org_id: CurrentOrgId):
    return db.scalars(
        select(ExecutiveBrief)
        .where(ExecutiveBrief.organization_id == org_id)
        .order_by(ExecutiveBrief.generated_at.desc())
    ).all()


@router.post("/generate", response_model=BriefOut, status_code=status.HTTP_201_CREATED)
def generate_brief(brief_type: str, db: DbDep, org_id: CurrentOrgId):
    try:
        return brief_generator.generate(db, org_id, brief_type)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
