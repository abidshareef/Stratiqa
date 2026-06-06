"""Report generator — produces consulting-style structured reports.

Each report has: Executive Summary, KPIs, Charts (chart specs), Risk Analysis,
Project Analysis, Recommendations, Appendix. Stored as structured JSON so the
frontend renders it as a premium deliverable (and can export to PDF later).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session as DBSession

from app.models.analytics import KPI
from app.models.goals import StrategicGoal
from app.models.projects import Project, ProjectRisk
from app.models.recommendations import Recommendation
from app.models.reporting import Report
from app.services import recommendation_engine

VALID_REPORT_TYPES = {"daily", "weekly", "monthly", "quarterly", "executive"}


def _kpi_section(db: DBSession, org_id: uuid.UUID) -> list[dict]:
    names = db.scalars(
        select(KPI.kpi_name).where(KPI.organization_id == org_id).distinct()
    ).all()
    out: list[dict] = []
    for name in names:
        latest = db.scalar(
            select(KPI)
            .where(KPI.organization_id == org_id, KPI.kpi_name == name)
            .order_by(KPI.recorded_at.desc())
        )
        if latest and latest.value is not None:
            out.append({"name": name, "value": float(latest.value)})
    return out


def _chart_specs(kpis: list[dict]) -> list[dict]:
    """Chart specifications consumed by the ECharts frontend (allowed types only)."""
    specs: list[dict] = []
    if kpis:
        specs.append(
            {
                "type": "bar",
                "title": "Current KPIs",
                "x": [k["name"] for k in kpis],
                "series": [k["value"] for k in kpis],
            }
        )
    return specs


def generate(
    db: DBSession,
    org_id: uuid.UUID,
    report_type: str,
    *,
    generated_by: uuid.UUID | None = None,
) -> Report:
    report_type = report_type.lower()
    if report_type not in VALID_REPORT_TYPES:
        raise ValueError(f"Invalid report type: {report_type}")

    kpis = _kpi_section(db, org_id)

    project_count = db.scalar(
        select(func.count(Project.id)).where(Project.organization_id == org_id)
    )
    active_projects = db.scalars(
        select(Project).where(
            Project.organization_id == org_id, Project.status != "completed"
        )
    ).all()

    risks = (
        db.scalars(
            select(ProjectRisk)
            .join(Project, Project.id == ProjectRisk.project_id)
            .where(
                Project.organization_id == org_id,
                ProjectRisk.risk_level.in_(["high", "critical"]),
            )
        ).all()
    )

    goals = db.scalars(
        select(StrategicGoal).where(
            StrategicGoal.organization_id == org_id, StrategicGoal.status == "active"
        )
    ).all()

    # Ensure recommendations are current, then read them.
    recommendation_engine.refresh_recommendations(db, org_id)
    recs = db.scalars(
        select(Recommendation).where(
            Recommendation.organization_id == org_id,
            Recommendation.status == "pending",
        )
    ).all()

    summary = (
        f"This {report_type} report covers {project_count} project(s), "
        f"{len(goals)} active strategic goal(s), and surfaces {len(risks)} high-severity "
        f"risk(s). {len(recs)} recommendation(s) are pending executive review."
    )

    content = {
        "executive_summary": summary,
        "kpis": kpis,
        "charts": _chart_specs(kpis),
        "risk_analysis": [
            {"title": r.risk_title, "level": r.risk_level, "impact": r.impact}
            for r in risks
        ],
        "project_analysis": [
            {"name": p.name, "status": p.status} for p in active_projects
        ],
        "recommendations": [
            {
                "title": r.title,
                "expected_impact": r.expected_impact,
                "confidence_score": float(r.confidence_score),
                "risk_level": r.risk_level,
            }
            for r in recs
        ],
        "appendix": {
            "generated_at": datetime.now(UTC).isoformat(),
            "methodology": "Rule-based analysis over live organizational data (MVP).",
        },
    }

    report = Report(
        organization_id=org_id,
        report_type=report_type,
        title=f"{report_type.capitalize()} Report — {datetime.now(UTC):%Y-%m-%d}",
        content=content,
        generated_by=generated_by,
    )
    db.add(report)
    db.flush()
    return report
