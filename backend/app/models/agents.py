"""Section 6: AI Agent Layer."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, UUIDPk
from app.models._types import fk

# Agent types from the schema.
AGENT_TYPES = (
    "STRATIQA_ONE",
    "FINANCE",
    "SALES",
    "HR",
    "OPERATIONS",
    "CUSTOMER_SUCCESS",
    "PRODUCT",
    "PROJECT",
    "RISK",
)


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[UUIDPk]
    organization_id = fk("organizations.id")
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    agent_type: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False)


class AgentTask(Base):
    __tablename__ = "agent_tasks"

    id: Mapped[UUIDPk]
    agent_id = fk("agents.id")
    task_type: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="queued", nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AgentInteraction(Base):
    __tablename__ = "agent_interactions"

    id: Mapped[UUIDPk]
    agent_id = fk("agents.id")
    query: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str | None] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
