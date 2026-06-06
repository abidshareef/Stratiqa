"""Strategic goal schemas."""

from __future__ import annotations

import uuid
from datetime import date

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class GoalCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    description: str | None = None
    goal_type: str | None = Field(default=None, max_length=60)
    target_value: float | None = None
    target_date: date | None = None


class GoalUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    goal_type: str | None = None
    target_value: float | None = None
    target_date: date | None = None
    status: str | None = None


class GoalOut(ORMModel):
    id: uuid.UUID
    title: str
    description: str | None
    goal_type: str | None
    target_value: float | None
    target_date: date | None
    status: str


class GoalProgressOut(ORMModel):
    id: uuid.UUID
    progress_percentage: float


class GoalDetail(GoalOut):
    latest_progress: float = 0.0
    completion_forecast: str | None = None
    risk_indicator: str = "on_track"
