"""Section 7: Memory Layer (organization / user / agent / project / decision)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, UUIDPk
from app.models._types import fk


class OrganizationMemory(Base):
    __tablename__ = "organization_memory"

    id: Mapped[UUIDPk]
    organization_id = fk("organizations.id")
    memory_type: Mapped[str] = mapped_column(String(60), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding_id: Mapped[str | None] = mapped_column(String(80))  # Qdrant point id
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class UserMemory(Base):
    __tablename__ = "user_memory"

    id: Mapped[UUIDPk]
    user_id = fk("users.id")
    memory_type: Mapped[str] = mapped_column(String(60), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AgentMemory(Base):
    __tablename__ = "agent_memory"

    id: Mapped[UUIDPk]
    agent_id = fk("agents.id")
    memory_type: Mapped[str] = mapped_column(String(60), nullable=False)
    memory_content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ProjectMemory(Base):
    __tablename__ = "project_memory"

    id: Mapped[UUIDPk]
    project_id = fk("projects.id")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class DecisionMemory(Base):
    __tablename__ = "decision_memory"

    id: Mapped[UUIDPk]
    organization_id = fk("organizations.id")
    decision_summary: Mapped[str] = mapped_column(Text, nullable=False)
    reasoning: Mapped[str | None] = mapped_column(Text)
    outcome: Mapped[str | None] = mapped_column(Text)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
