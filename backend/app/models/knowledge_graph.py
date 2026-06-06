"""Section 8: Knowledge Graph."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, UUIDPk
from app.models._types import fk


class Entity(Base):
    __tablename__ = "entities"

    id: Mapped[UUIDPk]
    organization_id = fk("organizations.id")
    entity_type: Mapped[str] = mapped_column(String(60), nullable=False)
    entity_name: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)


class Relationship(Base):
    __tablename__ = "relationships"

    id: Mapped[UUIDPk]
    source_entity = fk("entities.id")
    target_entity = fk("entities.id")
    relationship_type: Mapped[str] = mapped_column(String(80), nullable=False)


class GraphEvent(Base):
    __tablename__ = "graph_events"

    id: Mapped[UUIDPk]
    entity_id = fk("entities.id")
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    event_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
