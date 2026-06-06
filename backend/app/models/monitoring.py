"""Section 15: Alert & Monitoring (incl. Failure Intelligence)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, UUIDPk
from app.models._types import fk


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[UUIDPk]
    organization_id = fk("organizations.id")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="info", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="open", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[UUIDPk]
    organization_id = fk("organizations.id")
    incident_type: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class FailureEvent(Base):
    __tablename__ = "failure_events"

    id: Mapped[UUIDPk]
    organization_id = fk("organizations.id")
    failure_type: Mapped[str] = mapped_column(String(80), nullable=False)
    root_cause: Mapped[str | None] = mapped_column(Text)
    resolution: Mapped[str | None] = mapped_column(Text)


class RootCauseAnalysis(Base):
    __tablename__ = "root_cause_analysis"

    id: Mapped[UUIDPk]
    failure_event_id = fk("failure_events.id")
    analysis: Mapped[str | None] = mapped_column(Text)
    recommendation: Mapped[str | None] = mapped_column(Text)
