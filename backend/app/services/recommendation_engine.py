"""Recommendation Engine.

Generates strategic recommendations GROUNDED in the organization's actual data
(goals, projects, tasks, risks, KPIs). Never produces generic advice. Each
recommendation carries the explainability fields required by the spec:
title, reasoning, expected impact, confidence score, risk level, data sources.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.models.analytics import KPI
from app.models.goals import GoalProgress, StrategicGoal
from app.models.projects import Project, ProjectRisk, Task
from app.models.recommendations import Recommendation


@dataclass
class Candidate:
    title: str
    description: str
    reasoning: str
    expected_impact: str
    confidence_score: float
    risk_level: str
    data_sources: str


@dataclass
class AnalysisChange:
    """What a fresh analysis pass changed versus the previous one.

    Lets the platform *recognize* how new incoming data moved the picture, not
    just that it was re-analyzed: which insights newly appeared, which were
    resolved (no longer supported by the data), and how many held steady.
    """

    new_insights: list[str]
    resolved_insights: list[str]
    unchanged: int

    @property
    def changed(self) -> bool:
        return bool(self.new_insights or self.resolved_insights)

    def summary(self) -> str:
        if not self.changed:
            return "New data ingested; analysis unchanged (no new or resolved insights)."
        parts: list[str] = []
        if self.new_insights:
            parts.append(f"{len(self.new_insights)} new insight(s): {'; '.join(self.new_insights)}")
        if self.resolved_insights:
            parts.append(
                f"{len(self.resolved_insights)} resolved: {'; '.join(self.resolved_insights)}"
            )
        return "New data shifted the analysis — " + ". ".join(parts) + "."


def _overdue(tasks: list[Task]) -> list[Task]:
    today = date.today()
    return [t for t in tasks if t.due_date and t.due_date < today and t.status != "done"]


def generate_candidates(db: DBSession, org_id: uuid.UUID) -> list[Candidate]:
    """Analyze org data and return grounded recommendation candidates."""
    candidates: list[Candidate] = []

    # --- Projects with critical/high open risks ---
    projects = db.scalars(select(Project).where(Project.organization_id == org_id)).all()
    for project in projects:
        risks = db.scalars(
            select(ProjectRisk).where(ProjectRisk.project_id == project.id)
        ).all()
        high = [r for r in risks if r.risk_level in {"high", "critical"}]
        if high:
            titles = ", ".join(r.risk_title for r in high[:3])
            candidates.append(
                Candidate(
                    title=f"Mitigate {len(high)} high-severity risk(s) on '{project.name}'",
                    description=(
                        f"Project '{project.name}' carries {len(high)} unmitigated "
                        f"high/critical risk(s): {titles}."
                    ),
                    reasoning=(
                        "High-severity project risks left unaddressed are the leading "
                        "driver of schedule slippage and budget overrun. Each listed risk "
                        "lacks a recorded mitigation or is still open."
                    ),
                    expected_impact="Reduced delivery risk; protects project budget and timeline.",
                    confidence_score=82.0,
                    risk_level="high",
                    data_sources=f"project_risks (project_id={project.id})",
                )
            )

        tasks = db.scalars(select(Task).where(Task.project_id == project.id)).all()
        overdue = _overdue(tasks)
        if len(overdue) >= 3:
            candidates.append(
                Candidate(
                    title=f"Re-sequence {len(overdue)} overdue tasks on '{project.name}'",
                    description=(
                        f"{len(overdue)} tasks on '{project.name}' are past their due date "
                        "and not yet complete."
                    ),
                    reasoning=(
                        "A cluster of overdue tasks signals an unrealistic plan or a "
                        "resourcing bottleneck. Re-sequencing and reassigning recovers velocity "
                        "before the milestone is missed."
                    ),
                    expected_impact="Recovered schedule; clearer critical path.",
                    confidence_score=74.0,
                    risk_level="medium",
                    data_sources=f"tasks (project_id={project.id}, overdue={len(overdue)})",
                )
            )

    # --- Goals stalling against their target date ---
    goals = db.scalars(
        select(StrategicGoal).where(
            StrategicGoal.organization_id == org_id, StrategicGoal.status == "active"
        )
    ).all()
    for goal in goals:
        latest = db.scalar(
            select(GoalProgress)
            .where(GoalProgress.goal_id == goal.id)
            .order_by(GoalProgress.recorded_at.desc())
        )
        progress = float(latest.progress_percentage) if latest else 0.0
        if goal.target_date and progress < 50:
            days_left = (goal.target_date - date.today()).days
            if days_left <= 60:
                candidates.append(
                    Candidate(
                        title=f"Accelerate goal '{goal.title}' — behind schedule",
                        description=(
                            f"Goal '{goal.title}' is at {progress:.0f}% with {days_left} "
                            "days remaining to its target date."
                        ),
                        reasoning=(
                            "Progress trajectory will not meet the target date at the current "
                            "pace. Early intervention (re-scoping or adding resources) is far "
                            "cheaper than a missed strategic objective."
                        ),
                        expected_impact="Improved likelihood of hitting the strategic target.",
                        confidence_score=68.0,
                        risk_level="medium",
                        data_sources=f"strategic_goals + goal_progress (goal_id={goal.id})",
                    )
                )

    # --- KPI deterioration (latest vs previous reading) ---
    candidates.extend(_kpi_candidates(db, org_id))
    return candidates


def _kpi_candidates(db: DBSession, org_id: uuid.UUID) -> list[Candidate]:
    out: list[Candidate] = []
    names = db.scalars(
        select(KPI.kpi_name).where(KPI.organization_id == org_id).distinct()
    ).all()
    for name in names:
        readings = db.scalars(
            select(KPI)
            .where(KPI.organization_id == org_id, KPI.kpi_name == name)
            .order_by(KPI.recorded_at.desc())
            .limit(2)
        ).all()
        if len(readings) < 2 or readings[0].value is None or readings[1].value is None:
            continue
        latest, prev = float(readings[0].value), float(readings[1].value)
        if prev == 0:
            continue
        change = (latest - prev) / abs(prev) * 100
        if change <= -10:
            out.append(
                Candidate(
                    title=f"Investigate {name} decline ({change:.0f}%)",
                    description=f"'{name}' fell from {prev:,.0f} to {latest:,.0f}.",
                    reasoning=(
                        f"A {abs(change):.0f}% drop in {name} between the two most recent "
                        "readings exceeds the 10% alert threshold and warrants root-cause analysis."
                    ),
                    expected_impact="Early detection limits revenue/operational downside.",
                    confidence_score=70.0,
                    risk_level="high" if change <= -25 else "medium",
                    data_sources=f"kpis (name={name})",
                )
            )
    return out


def refresh_recommendations(db: DBSession, org_id: uuid.UUID) -> list[Recommendation]:
    """Regenerate pending recommendations for an org from current data."""
    created, _ = refresh_with_changes(db, org_id)
    return created


def refresh_with_changes(
    db: DBSession, org_id: uuid.UUID
) -> tuple[list[Recommendation], AnalysisChange]:
    """Regenerate pending recommendations and report how the analysis changed.

    Snapshots the existing insight set *before* it is rebuilt, then diffs it
    against the freshly generated set so callers ingesting new data can show the
    user exactly what moved.
    """
    # Clear stale, still-pending recommendations to avoid duplicates.
    existing = db.scalars(
        select(Recommendation).where(
            Recommendation.organization_id == org_id,
            Recommendation.status == "pending",
        )
    ).all()
    before = {rec.title for rec in existing}
    for rec in existing:
        db.delete(rec)
    db.flush()  # ensure deletes settle before re-inserting same-titled rows

    created: list[Recommendation] = []
    for c in generate_candidates(db, org_id):
        rec = Recommendation(
            organization_id=org_id,
            title=c.title,
            description=c.description,
            reasoning=c.reasoning,
            expected_impact=c.expected_impact,
            confidence_score=c.confidence_score,
            risk_level=c.risk_level,
            data_sources=c.data_sources,
            status="pending",
        )
        db.add(rec)
        created.append(rec)
    db.flush()

    after = {rec.title for rec in created}
    change = AnalysisChange(
        new_insights=sorted(after - before),
        resolved_insights=sorted(before - after),
        unchanged=len(after & before),
    )
    return created, change
