"""Project intelligence schemas."""

from __future__ import annotations

import uuid
from datetime import date

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str | None = None
    budget: float | None = None
    status: str = "planning"
    start_date: date | None = None
    end_date: date | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    budget: float | None = None
    status: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class ProjectOut(ORMModel):
    id: uuid.UUID
    name: str
    description: str | None
    budget: float | None
    status: str
    start_date: date | None
    end_date: date | None


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    priority: str = "medium"
    status: str = "todo"
    due_date: date | None = None


class TaskOut(ORMModel):
    id: uuid.UUID
    title: str
    description: str | None
    priority: str
    status: str
    due_date: date | None


class MilestoneOut(ORMModel):
    id: uuid.UUID
    title: str
    due_date: date | None
    status: str


class ProjectRiskOut(ORMModel):
    id: uuid.UUID
    risk_title: str
    risk_level: str
    impact: str | None
    mitigation: str | None


class ProjectHealth(BaseModel):
    score: int  # 0-100
    label: str  # healthy / at_risk / critical
    open_tasks: int
    overdue_tasks: int
    open_risks: int
    drivers: list[str]


class ProjectDetail(ProjectOut):
    # Defaults let ProjectDetail.model_validate(project) succeed from a bare ORM
    # Project; the endpoint then populates these from related queries.
    health: ProjectHealth | None = None
    tasks: list[TaskOut] = Field(default_factory=list)
    milestones: list[MilestoneOut] = Field(default_factory=list)
    risks: list[ProjectRiskOut] = Field(default_factory=list)
