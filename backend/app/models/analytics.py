"""Section 10: KPI & Analytics."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, UUIDPk
from app.models._types import JSONB, fk


class KPI(Base):
    __tablename__ = "kpis"

    id: Mapped[UUIDPk]
    organization_id = fk("organizations.id")
    kpi_name: Mapped[str] = mapped_column(String(120), nullable=False)
    value: Mapped[float | None] = mapped_column(Numeric(18, 2))
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Forecast(Base):
    __tablename__ = "forecasts"

    id: Mapped[UUIDPk]
    organization_id = fk("organizations.id")
    forecast_type: Mapped[str] = mapped_column(String(80), nullable=False)
    forecast_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Anomaly(Base):
    __tablename__ = "anomalies"

    id: Mapped[UUIDPk]
    organization_id = fk("organizations.id")
    anomaly_type: Mapped[str] = mapped_column(String(80), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[UUIDPk]
    organization_id = fk("organizations.id")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    estimated_impact: Mapped[str | None] = mapped_column(Text)
    recommendation: Mapped[str | None] = mapped_column(Text)
