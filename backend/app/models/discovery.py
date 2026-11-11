"""Section 3: Business Discovery Engine."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, UUIDPk
from app.models._types import JSONB, fk


class BusinessProfile(Base):
    __tablename__ = "business_profiles"

    id: Mapped[UUIDPk]
    organization_id = fk("organizations.id")
    industry: Mapped[str | None] = mapped_column(String(120))
    business_model: Mapped[str | None] = mapped_column(String(120))
    company_size: Mapped[str | None] = mapped_column(String(60))
    annual_revenue: Mapped[float | None] = mapped_column(Numeric(18, 2))
    employee_count: Mapped[int | None] = mapped_column(BigInteger)


class BusinessDNA(Base):
    __tablename__ = "business_dna"

    id: Mapped[UUIDPk]
    organization_id = fk("organizations.id")
    growth_stage: Mapped[str | None] = mapped_column(String(60))
    risk_profile: Mapped[str | None] = mapped_column(String(60))
    operational_complexity: Mapped[str | None] = mapped_column(String(60))
    market_type: Mapped[str | None] = mapped_column(String(60))
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class BusinessBlueprint(Base):
    __tablename__ = "business_blueprints"

    id: Mapped[UUIDPk]
    organization_id = fk("organizations.id")
    blueprint_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
