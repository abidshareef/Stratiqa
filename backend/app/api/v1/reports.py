"""Report endpoints — generate and retrieve consulting-style reports."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.deps import CurrentOrgId, CurrentUser, DbDep
from app.models.reporting import Report
from app.schemas.report import ReportOut, ReportSummary
from app.services import report_generator

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("", response_model=list[ReportSummary])
def list_reports(db: DbDep, org_id: CurrentOrgId):
    return db.scalars(
        select(Report)
        .where(Report.organization_id == org_id)
        .order_by(Report.created_at.desc())
    ).all()


@router.post("/generate", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
def generate_report(report_type: str, db: DbDep, org_id: CurrentOrgId, user: CurrentUser):
    try:
        report = report_generator.generate(
            db, org_id, report_type, generated_by=user.id
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    return report


@router.get("/{report_id}", response_model=ReportOut)
def get_report(report_id: uuid.UUID, db: DbDep, org_id: CurrentOrgId):
    report = db.get(Report, report_id)
    if report is None or report.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return report
