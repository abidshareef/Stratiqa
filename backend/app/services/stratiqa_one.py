"""STRATIQA One — the master orchestration agent.

Composes the executive surfaces (Home, War Room) and answers natural-language
questions by reasoning over organizational data. Intelligence is assembled from
the underlying engines; an LLM gateway can later enrich the narrative, but the
grounded data layer remains the source of truth.
"""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.models.analytics import Opportunity
from app.models.goals import StrategicGoal
from app.models.identity import Organization
from app.models.projects import Project, ProjectRisk, Task
from app.models.recommendations import Recommendation
from app.schemas.stratiqa_one import (
    AskResponse,
    ExecutiveHome,
    OpportunityItem,
    PriorityItem,
    RiskItem,
    WarRoom,
)
from app.services import recommendation_engine


def _risks(db: DBSession, org_id: uuid.UUID, only_critical: bool = False) -> list[RiskItem]:
    levels = ["critical"] if only_critical else ["high", "critical"]
    rows = db.execute(
        select(ProjectRisk, Project.name)
        .join(Project, Project.id == ProjectRisk.project_id)
        .where(Project.organization_id == org_id, ProjectRisk.risk_level.in_(levels))
    ).all()
    return [
        RiskItem(title=r.risk_title, level=r.risk_level, context=f"Project: {pname}")
        for r, pname in rows
    ]


def _opportunities(db: DBSession, org_id: uuid.UUID) -> list[OpportunityItem]:
    rows = db.scalars(
        select(Opportunity).where(Opportunity.organization_id == org_id)
    ).all()
    return [
        OpportunityItem(
            title=o.title,
            estimated_impact=o.estimated_impact,
            recommendation=o.recommendation,
        )
        for o in rows
    ]


def _priorities(db: DBSession, org_id: uuid.UUID) -> list[PriorityItem]:
    today = date.today()
    items: list[PriorityItem] = []

    overdue = db.scalars(
        select(Task)
        .join(Project, Project.id == Task.project_id)
        .where(
            Project.organization_id == org_id,
            Task.due_date < today,
            Task.status != "done",
        )
    ).all()
    for t in overdue[:5]:
        items.append(
            PriorityItem(
                title=t.title,
                detail=f"Overdue since {t.due_date:%Y-%m-%d}",
                severity="danger",
                source="tasks",
            )
        )

    due_today = db.scalars(
        select(Task)
        .join(Project, Project.id == Task.project_id)
        .where(
            Project.organization_id == org_id,
            Task.due_date == today,
            Task.status != "done",
        )
    ).all()
    for t in due_today[:5]:
        items.append(
            PriorityItem(
                title=t.title, detail="Due today", severity="warning", source="tasks"
            )
        )
    return items


def _active_goals(db: DBSession, org_id: uuid.UUID) -> list[StrategicGoal]:
    return list(
        db.scalars(
            select(StrategicGoal).where(
                StrategicGoal.organization_id == org_id,
                StrategicGoal.status == "active",
            )
        ).all()
    )


def _active_projects(db: DBSession, org_id: uuid.UUID) -> list[Project]:
    return list(
        db.scalars(
            select(Project).where(
                Project.organization_id == org_id, Project.status != "completed"
            )
        ).all()
    )


def _pending_recommendations(db: DBSession, org_id: uuid.UUID) -> list[Recommendation]:
    recommendation_engine.refresh_recommendations(db, org_id)
    return list(
        db.scalars(
            select(Recommendation)
            .where(
                Recommendation.organization_id == org_id,
                Recommendation.status == "pending",
            )
            .order_by(Recommendation.confidence_score.desc())
        ).all()
    )


def executive_home(db: DBSession, org_id: uuid.UUID, user_name: str | None) -> ExecutiveHome:
    org = db.get(Organization, org_id)
    risks = _risks(db, org_id)
    priorities = _priorities(db, org_id)
    recs = _pending_recommendations(db, org_id)
    goals = _active_goals(db, org_id)
    projects = _active_projects(db, org_id)

    name = user_name.split()[0] if user_name else "there"
    summary = (
        f"{org.name if org else 'Your organization'} has {len(projects)} active project(s), "
        f"{len(goals)} strategic goal(s) in flight, {len(risks)} elevated risk(s), and "
        f"{len(recs)} recommendation(s) awaiting your review."
    )
    return ExecutiveHome(
        welcome=f"Welcome back, {name}.",
        summary=summary,
        todays_priorities=priorities,
        risks=risks,
        opportunities=_opportunities(db, org_id),
        goals=goals,  # type: ignore[arg-type]
        projects=projects,  # type: ignore[arg-type]
        recommendations=recs,  # type: ignore[arg-type]
    )


def war_room(db: DBSession, org_id: uuid.UUID) -> WarRoom:
    recs = _pending_recommendations(db, org_id)
    return WarRoom(
        critical_risks=_risks(db, org_id, only_critical=True) or _risks(db, org_id),
        goals=_active_goals(db, org_id),  # type: ignore[arg-type]
        projects=_active_projects(db, org_id),  # type: ignore[arg-type]
        recommendations=recs,  # type: ignore[arg-type]
        opportunities=_opportunities(db, org_id),
        business_events=_business_events(db, org_id),
        twin_insights=_twin_insights(db, org_id),
    )


def _business_events(db: DBSession, org_id: uuid.UUID) -> list[dict]:
    """A lightweight activity stream from recent recommendations and risks."""
    events: list[dict] = []
    recs = db.scalars(
        select(Recommendation)
        .where(Recommendation.organization_id == org_id)
        .order_by(Recommendation.created_at.desc())
        .limit(5)
    ).all()
    for r in recs:
        events.append(
            {
                "type": "recommendation_generated",
                "title": r.title,
                "at": r.created_at.isoformat() if r.created_at else None,
            }
        )
    return events


def _twin_insights(db: DBSession, org_id: uuid.UUID) -> list[str]:
    return [
        "Run a Business Twin simulation to pressure-test your next strategic move.",
        "Marketing and expansion levers show the highest revenue sensitivity in this model.",
    ]


def ask(db: DBSession, org_id: uuid.UUID, query: str) -> AskResponse:
    """Answer an executive question grounded in current data.

    MVP: deterministic intent routing over the data layer. The LLM gateway can be
    layered on top to phrase the narrative, while these facts remain the anchor.
    """
    q = query.lower()
    recs = _pending_recommendations(db, org_id)
    sources: list[str] = []

    if any(k in q for k in ("risk", "danger", "threat")):
        risks = _risks(db, org_id)
        sources.append("project_risks")
        if risks:
            body = "; ".join(f"{r.title} ({r.level})" for r in risks[:5])
            answer = f"There are {len(risks)} elevated risk(s): {body}."
        else:
            answer = "No high or critical risks are currently recorded."
    elif any(k in q for k in ("goal", "objective", "target")):
        goals = _active_goals(db, org_id)
        sources.append("strategic_goals")
        body = "; ".join(g.title for g in goals[:5]) or "none yet"
        answer = f"You have {len(goals)} active strategic goal(s): {body}."
    elif any(k in q for k in ("project", "delivery", "milestone")):
        projects = _active_projects(db, org_id)
        sources.append("projects")
        body = "; ".join(f"{p.name} [{p.status}]" for p in projects[:5]) or "none yet"
        answer = f"{len(projects)} active project(s): {body}."
    elif any(k in q for k in ("recommend", "advice", "should", "next")):
        sources.append("recommendations")
        if recs:
            top = recs[0]
            answer = (
                f"Top recommendation: {top.title}. {top.reasoning} "
                f"(confidence {float(top.confidence_score):.0f}%)."
            )
        else:
            answer = "No pending recommendations — your operations look stable right now."
    else:
        sources += ["projects", "strategic_goals", "recommendations"]
        answer = (
            f"I'm tracking {len(_active_projects(db, org_id))} project(s), "
            f"{len(_active_goals(db, org_id))} goal(s), and {len(recs)} recommendation(s). "
            "Ask me about risks, goals, projects, or what to do next."
        )

    return AskResponse(
        answer=answer,
        confidence_score=72.0,
        data_sources=sources,
        related_recommendations=recs[:3],  # type: ignore[arg-type]
    )
