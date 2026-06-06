"""Project intelligence endpoints — CRUD plus a computed health indicator."""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.deps import CurrentOrgId, DbDep
from app.models.projects import Milestone, Project, ProjectRisk, Task
from app.schemas.project import (
    MilestoneOut,
    ProjectCreate,
    ProjectDetail,
    ProjectHealth,
    ProjectOut,
    ProjectRiskOut,
    ProjectUpdate,
    TaskCreate,
    TaskOut,
)

router = APIRouter(prefix="/projects", tags=["projects"])


def _get_owned(db, org_id: uuid.UUID, project_id: uuid.UUID) -> Project:
    project = db.get(Project, project_id)
    if project is None or project.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


def compute_health(tasks: list[Task], risks: list[ProjectRisk]) -> ProjectHealth:
    today = date.today()
    open_tasks = [t for t in tasks if t.status != "done"]
    overdue = [t for t in open_tasks if t.due_date and t.due_date < today]
    open_risks = [r for r in risks if r.risk_level in {"high", "critical"}]

    score = 100
    drivers: list[str] = []
    if overdue:
        penalty = min(40, len(overdue) * 10)
        score -= penalty
        drivers.append(f"{len(overdue)} overdue task(s)")
    if open_risks:
        penalty = min(40, len(open_risks) * 15)
        score -= penalty
        drivers.append(f"{len(open_risks)} high/critical risk(s)")
    if open_tasks and len(open_tasks) > 20:
        score -= 10
        drivers.append("large open task backlog")

    score = max(0, score)
    label = "healthy" if score >= 75 else "at_risk" if score >= 45 else "critical"
    if not drivers:
        drivers.append("No blocking issues detected")
    return ProjectHealth(
        score=score,
        label=label,
        open_tasks=len(open_tasks),
        overdue_tasks=len(overdue),
        open_risks=len(open_risks),
        drivers=drivers,
    )


@router.get("", response_model=list[ProjectOut])
def list_projects(db: DbDep, org_id: CurrentOrgId):
    return db.scalars(select(Project).where(Project.organization_id == org_id)).all()


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: DbDep, org_id: CurrentOrgId):
    project = Project(organization_id=org_id, **payload.model_dump())
    db.add(project)
    db.flush()
    return project


@router.get("/{project_id}", response_model=ProjectDetail)
def get_project(project_id: uuid.UUID, db: DbDep, org_id: CurrentOrgId):
    project = _get_owned(db, org_id, project_id)
    tasks = db.scalars(select(Task).where(Task.project_id == project.id)).all()
    milestones = db.scalars(
        select(Milestone).where(Milestone.project_id == project.id)
    ).all()
    risks = db.scalars(
        select(ProjectRisk).where(ProjectRisk.project_id == project.id)
    ).all()

    detail = ProjectDetail.model_validate(project)
    detail.health = compute_health(list(tasks), list(risks))
    detail.tasks = [TaskOut.model_validate(t) for t in tasks]
    detail.milestones = [MilestoneOut.model_validate(m) for m in milestones]
    detail.risks = [ProjectRiskOut.model_validate(r) for r in risks]
    return detail


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: uuid.UUID, payload: ProjectUpdate, db: DbDep, org_id: CurrentOrgId
):
    project = _get_owned(db, org_id, project_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    db.flush()
    return project


@router.post(
    "/{project_id}/tasks", response_model=TaskOut, status_code=status.HTTP_201_CREATED
)
def add_task(
    project_id: uuid.UUID, payload: TaskCreate, db: DbDep, org_id: CurrentOrgId
):
    _get_owned(db, org_id, project_id)
    task = Task(project_id=project_id, **payload.model_dump())
    db.add(task)
    db.flush()
    return task
