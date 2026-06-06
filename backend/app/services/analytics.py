"""Analytics service — assembles the executive dashboard's quantitative layer.

Reads KPI time-series, goal-progress trends, and project health from the
organization's actual data. All numbers are grounded; nothing is synthesized
at request time.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.models.analytics import KPI
from app.models.goals import GoalProgress, StrategicGoal
from app.models.projects import Project, ProjectRisk, Task
from app.schemas.analytics import (
    AnalyticsOverview,
    GoalProgressOut,
    KpiCard,
    ProjectHealthOut,
    TimeSeries,
)

# KPI display metadata. `lower_is_better` flips the "positive" judgement so a
# falling burn rate reads as good while falling revenue reads as bad.
KPI_META: dict[str, dict] = {
    "Monthly Revenue": {"unit": "$", "fmt": "currency", "lower_is_better": False},
    "MRR": {"unit": "$", "fmt": "currency", "lower_is_better": False},
    "Gross Margin": {"unit": "%", "fmt": "percent", "lower_is_better": False},
    "Active Customers": {"unit": "", "fmt": "number", "lower_is_better": False},
    "Net Burn": {"unit": "$", "fmt": "currency", "lower_is_better": True},
    "Cash Runway": {"unit": "mo", "fmt": "number", "lower_is_better": False},
    "NPS": {"unit": "", "fmt": "number", "lower_is_better": False},
    "CAC": {"unit": "$", "fmt": "currency", "lower_is_better": True},
}

# Cards surfaced on the dashboard, in order.
DASHBOARD_KPIS = [
    "Monthly Revenue",
    "MRR",
    "Gross Margin",
    "Active Customers",
    "Net Burn",
    "Cash Runway",
]


def _kpi_series(db: DBSession, org_id: uuid.UUID, name: str) -> list[KPI]:
    return list(
        db.scalars(
            select(KPI)
            .where(KPI.organization_id == org_id, KPI.kpi_name == name)
            .order_by(KPI.recorded_at.asc())
        ).all()
    )


def _build_card(name: str, rows: list[KPI]) -> KpiCard | None:
    if not rows:
        return None
    meta = KPI_META.get(name, {"unit": "", "fmt": "number", "lower_is_better": False})
    series = [float(r.value) for r in rows if r.value is not None]
    if not series:
        return None

    value = series[-1]
    delta_pct: float | None = None
    direction = "flat"
    if len(series) >= 2 and series[-2] != 0:
        delta_pct = round((series[-1] - series[-2]) / abs(series[-2]) * 100, 1)
        if delta_pct > 0.5:
            direction = "up"
        elif delta_pct < -0.5:
            direction = "down"

    lower_is_better = bool(meta["lower_is_better"])
    if direction == "flat":
        positive = True
    else:
        rising = direction == "up"
        positive = rising != lower_is_better

    return KpiCard(
        key=name.lower().replace(" ", "_"),
        label=name,
        value=value,
        unit=meta["unit"],
        fmt=meta["fmt"],
        delta_pct=delta_pct,
        direction=direction,
        positive=positive,
        series=series,
    )


def _revenue_trend(db: DBSession, org_id: uuid.UUID) -> TimeSeries:
    rows = _kpi_series(db, org_id, "Monthly Revenue")
    return TimeSeries(
        labels=[r.recorded_at.strftime("%b") for r in rows],
        values=[float(r.value) for r in rows if r.value is not None],
    )


def _goal_progress(db: DBSession, org_id: uuid.UUID) -> list[GoalProgressOut]:
    goals = db.scalars(
        select(StrategicGoal).where(
            StrategicGoal.organization_id == org_id,
            StrategicGoal.status == "active",
        )
    ).all()
    out: list[GoalProgressOut] = []
    for g in goals:
        readings = db.scalars(
            select(GoalProgress)
            .where(GoalProgress.goal_id == g.id)
            .order_by(GoalProgress.recorded_at.asc())
        ).all()
        series = [float(r.progress_percentage) for r in readings]
        out.append(
            GoalProgressOut(
                title=g.title,
                progress=series[-1] if series else 0.0,
                target_date=g.target_date.isoformat() if g.target_date else None,
                status=g.status,
                series=series,
            )
        )
    return out


def _project_health(db: DBSession, org_id: uuid.UUID) -> list[ProjectHealthOut]:
    today = date.today()
    projects = db.scalars(
        select(Project).where(
            Project.organization_id == org_id, Project.status != "completed"
        )
    ).all()
    out: list[ProjectHealthOut] = []
    for p in projects:
        risks = db.scalars(
            select(ProjectRisk).where(ProjectRisk.project_id == p.id)
        ).all()
        open_high = sum(1 for r in risks if r.risk_level in {"high", "critical"})
        tasks = db.scalars(select(Task).where(Task.project_id == p.id)).all()
        overdue = sum(
            1 for t in tasks if t.due_date and t.due_date < today and t.status != "done"
        )
        score = max(0, min(100, 100 - open_high * 20 - overdue * 6))
        label = "healthy" if score >= 75 else "at_risk" if score >= 45 else "critical"
        out.append(
            ProjectHealthOut(
                name=p.name,
                score=score,
                label=label,
                open_risks=open_high,
                overdue_tasks=overdue,
            )
        )
    return out


def overview(db: DBSession, org_id: uuid.UUID) -> AnalyticsOverview:
    cards: list[KpiCard] = []
    for name in DASHBOARD_KPIS:
        card = _build_card(name, _kpi_series(db, org_id, name))
        if card:
            cards.append(card)
    return AnalyticsOverview(
        kpis=cards,
        revenue_trend=_revenue_trend(db, org_id),
        goal_progress=_goal_progress(db, org_id),
        project_health=_project_health(db, org_id),
        generated_at=datetime.utcnow(),
    )
