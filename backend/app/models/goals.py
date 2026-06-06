"""Section 4: Strategic Goal Engine."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, UUIDPk
from app.models._types import fk


class StrategicGoal(Base):
    __tablename__ = "strategic_goals"

    id: Mapped[UUIDPk]
    organization_id = fk("organizations.id")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    goal_type: Mapped[str | None] = mapped_column(String(60))
    target_value: Mapped[float | None] = mapped_column(Numeric(18, 2))
    target_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class GoalMetric(Base):
    __tablename__ = "goal_metrics"

    id: Mapped[UUIDPk]
    goal_id = fk("strategic_goals.id")
    metric_name: Mapped[str] = mapped_column(String(120), nullable=False)
    current_value: Mapped[float | None] = mapped_column(Numeric(18, 2))
    target_value: Mapped[float | None] = mapped_column(Numeric(18, 2))


class GoalProgress(Base):
    __tablename__ = "goal_progress"

    id: Mapped[UUIDPk]
    goal_id = fk("strategic_goals.id")
    progress_percentage: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
