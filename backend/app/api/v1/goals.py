"""Strategic goal endpoints with progress tracking and completion forecasting."""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.deps import CurrentOrgId, DbDep
from app.models.goals import GoalProgress, StrategicGoal
from app.schemas.goal import GoalCreate, GoalDetail, GoalOut, GoalUpdate

router = APIRouter(prefix="/goals", tags=["goals"])


def _get_owned(db, org_id: uuid.UUID, goal_id: uuid.UUID) -> StrategicGoal:
    goal = db.get(StrategicGoal, goal_id)
    if goal is None or goal.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    return goal


@router.get("", response_model=list[GoalOut])
def list_goals(db: DbDep, org_id: CurrentOrgId):
    return db.scalars(
        select(StrategicGoal).where(StrategicGoal.organization_id == org_id)
    ).all()


@router.post("", response_model=GoalOut, status_code=status.HTTP_201_CREATED)
def create_goal(payload: GoalCreate, db: DbDep, org_id: CurrentOrgId):
    goal = StrategicGoal(organization_id=org_id, **payload.model_dump())
    db.add(goal)
    db.flush()
    return goal


@router.get("/{goal_id}", response_model=GoalDetail)
def get_goal(goal_id: uuid.UUID, db: DbDep, org_id: CurrentOrgId):
    goal = _get_owned(db, org_id, goal_id)
    latest = db.scalar(
        select(GoalProgress)
        .where(GoalProgress.goal_id == goal.id)
        .order_by(GoalProgress.recorded_at.desc())
    )
    progress = float(latest.progress_percentage) if latest else 0.0

    forecast, risk = _forecast(goal, progress)
    detail = GoalDetail.model_validate(goal)
    detail.latest_progress = progress
    detail.completion_forecast = forecast
    detail.risk_indicator = risk
    return detail


@router.patch("/{goal_id}", response_model=GoalOut)
def update_goal(goal_id: uuid.UUID, payload: GoalUpdate, db: DbDep, org_id: CurrentOrgId):
    goal = _get_owned(db, org_id, goal_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(goal, field, value)
    db.flush()
    return goal


@router.post("/{goal_id}/progress", response_model=GoalDetail)
def record_progress(
    goal_id: uuid.UUID, percentage: float, db: DbDep, org_id: CurrentOrgId
):
    goal = _get_owned(db, org_id, goal_id)
    db.add(GoalProgress(goal_id=goal.id, progress_percentage=percentage))
    if percentage >= 100:
        goal.status = "completed"
    db.flush()
    return get_goal(goal_id, db, org_id)


def _forecast(goal: StrategicGoal, progress: float) -> tuple[str, str]:
    if goal.status == "completed" or progress >= 100:
        return "Completed", "complete"
    if not goal.target_date:
        return "No target date set", "unknown"
    days_left = (goal.target_date - date.today()).days
    if days_left < 0:
        return "Target date passed", "overdue"
    if progress >= 75 or days_left > 90:
        return f"On track ({progress:.0f}% with {days_left}d left)", "on_track"
    if progress < 40 and days_left <= 30:
        return f"At risk ({progress:.0f}% with only {days_left}d left)", "at_risk"
    return f"Monitor ({progress:.0f}% with {days_left}d left)", "monitor"
