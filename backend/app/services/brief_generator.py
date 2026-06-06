"""Executive brief generator — Morning and Evening briefs.

Morning: priorities, emerging risks, recommended actions, goal status.
Evening: achievements, issues, learnings, tomorrow's priorities.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.models.goals import StrategicGoal
from app.models.projects import Project, ProjectRisk, Task
from app.models.reporting import ExecutiveBrief
from app.services import recommendation_engine

VALID_BRIEF_TYPES = {"morning", "evening", "weekly", "monthly"}


def _high_risks(db: DBSession, org_id: uuid.UUID) -> list[ProjectRisk]:
    return list(
        db.scalars(
            select(ProjectRisk)
            .join(Project, Project.id == ProjectRisk.project_id)
            .where(
                Project.organization_id == org_id,
                ProjectRisk.risk_level.in_(["high", "critical"]),
            )
        ).all()
    )


def _morning_content(db: DBSession, org_id: uuid.UUID) -> dict:
    today = date.today()
    due_today = db.scalars(
        select(Task)
        .join(Project, Project.id == Task.project_id)
        .where(
            Project.organization_id == org_id,
            Task.due_date == today,
            Task.status != "done",
        )
    ).all()
    risks = _high_risks(db, org_id)
    recs = recommendation_engine.refresh_recommendations(db, org_id)
    goals = db.scalars(
        select(StrategicGoal).where(
            StrategicGoal.organization_id == org_id, StrategicGoal.status == "active"
        )
    ).all()

    return {
        "todays_priorities": [
            {"title": t.title, "priority": t.priority} for t in due_today
        ]
        or [{"title": "No tasks due today — focus on strategic goals", "priority": "info"}],
        "emerging_risks": [
            {"title": r.risk_title, "level": r.risk_level} for r in risks
        ],
        "recommended_actions": [
            {"title": r.title, "expected_impact": r.expected_impact} for r in recs[:5]
        ],
        "goal_status": [
            {"title": g.title, "status": g.status} for g in goals
        ],
    }


def _evening_content(db: DBSession, org_id: uuid.UUID) -> dict:
    today = date.today()
    completed_today = db.scalars(
        select(Task)
        .join(Project, Project.id == Task.project_id)
        .where(
            Project.organization_id == org_id,
            Task.status == "done",
            Task.updated_at >= datetime.combine(today, datetime.min.time()),
        )
    ).all()
    risks = _high_risks(db, org_id)
    overdue = db.scalars(
        select(Task)
        .join(Project, Project.id == Task.project_id)
        .where(
            Project.organization_id == org_id,
            Task.due_date < today,
            Task.status != "done",
        )
    ).all()

    return {
        "achievements": [{"title": t.title} for t in completed_today]
        or [{"title": "No tasks completed today"}],
        "issues": [{"title": t.title, "reason": "overdue"} for t in overdue],
        "new_risks": [{"title": r.risk_title, "level": r.risk_level} for r in risks],
        "learnings": [
            "Review overdue items for systemic bottlenecks"
            if overdue
            else "Steady execution — maintain momentum"
        ],
        "tomorrow_priorities": [{"title": t.title} for t in overdue[:5]],
    }


def generate(db: DBSession, org_id: uuid.UUID, brief_type: str) -> ExecutiveBrief:
    brief_type = brief_type.lower()
    if brief_type not in VALID_BRIEF_TYPES:
        raise ValueError(f"Invalid brief type: {brief_type}")

    if brief_type == "evening":
        content = _evening_content(db, org_id)
    else:
        content = _morning_content(db, org_id)
    content["generated_at"] = datetime.now(UTC).isoformat()

    brief = ExecutiveBrief(organization_id=org_id, brief_type=brief_type, content=content)
    db.add(brief)
    db.flush()
    return brief
