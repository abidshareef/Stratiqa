"""Section 12: Customer Intelligence."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, UUIDPk
from app.models._types import fk


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[UUIDPk]
    organization_id = fk("organizations.id")
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    segment: Mapped[str | None] = mapped_column(String(80))


class CustomerHealth(Base):
    __tablename__ = "customer_health"

    id: Mapped[UUIDPk]
    customer_id = fk("customers.id")
    health_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    churn_risk: Mapped[float | None] = mapped_column(Numeric(5, 2))


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id: Mapped[UUIDPk]
    customer_id = fk("customers.id")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="open", nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)


class CustomerInsight(Base):
    __tablename__ = "customer_insights"

    id: Mapped[UUIDPk]
    customer_id = fk("customers.id")
    insight: Mapped[str] = mapped_column(Text, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
