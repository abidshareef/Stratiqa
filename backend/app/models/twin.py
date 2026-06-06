"""Section 9: Digital Business Twin."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, UUIDPk
from app.models._types import fk


class TwinModel(Base):
    __tablename__ = "twin_models"

    id: Mapped[UUIDPk]
    organization_id = fk("organizations.id")
    model_name: Mapped[str] = mapped_column(String(120), nullable=False)
    version: Mapped[str] = mapped_column(String(20), default="1.0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class TwinSnapshot(Base):
    __tablename__ = "twin_snapshots"

    id: Mapped[UUIDPk]
    model_id = fk("twin_models.id")
    snapshot_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Simulation(Base):
    __tablename__ = "simulations"

    id: Mapped[UUIDPk]
    organization_id = fk("organizations.id")
    scenario_name: Mapped[str] = mapped_column(String(255), nullable=False)
    scenario_description: Mapped[str | None] = mapped_column(Text)
    inputs: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class SimulationResult(Base):
    __tablename__ = "simulation_results"

    id: Mapped[UUIDPk]
    simulation_id = fk("simulations.id")
    predicted_outcome: Mapped[dict] = mapped_column(JSONB, default=dict)
    confidence_score: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
