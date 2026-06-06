"""Section 5: Project Intelligence."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDPk
from app.models._types import fk, fk_optional


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[UUIDPk]
    organization_id = fk("organizations.id")
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    owner_id = fk_optional("users.id")
    budget: Mapped[float | None] = mapped_column(Numeric(18, 2))
    status: Mapped[str] = mapped_column(String(40), default="planning", nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)


class Milestone(Base):
    __tablename__ = "milestones"

    id: Mapped[UUIDPk]
    project_id = fk("projects.id")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(40), default="pending", nullable=False)


class Task(Base, TimestampMixin):
    __tablename__ = "tasks"

    id: Mapped[UUIDPk]
    project_id = fk("projects.id")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    assigned_to = fk_optional("users.id")
    priority: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="todo", nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date)


class TaskDependency(Base):
    __tablename__ = "task_dependencies"

    id: Mapped[UUIDPk]
    task_id = fk("tasks.id")
    depends_on_task = fk("tasks.id")


class ProjectRisk(Base):
    __tablename__ = "project_risks"

    id: Mapped[UUIDPk]
    project_id = fk("projects.id")
    risk_title: Mapped[str] = mapped_column(String(255), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    impact: Mapped[str | None] = mapped_column(Text)
    mitigation: Mapped[str | None] = mapped_column(Text)
