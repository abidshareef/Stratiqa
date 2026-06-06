"""Section 16: Audit & Governance."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, UUIDPk
from app.models._types import fk, fk_optional


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[UUIDPk]
    user_id = fk_optional("users.id")
    organization_id = fk_optional("organizations.id")
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    resource: Mapped[str | None] = mapped_column(String(120))
    detail: Mapped[str | None] = mapped_column(Text)
    ip_address: Mapped[str | None] = mapped_column(String(64))
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[UUIDPk]
    organization_id = fk("organizations.id")
    provider_name: Mapped[str] = mapped_column(String(80), nullable=False)
    encrypted_key: Mapped[str] = mapped_column(Text, nullable=False)


class GovernanceRecord(Base):
    __tablename__ = "governance_records"

    id: Mapped[UUIDPk]
    organization_id = fk("organizations.id")
    decision_id = fk_optional("decision_memory.id")
    confidence_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    data_sources: Mapped[dict] = mapped_column(JSONB, default=dict)
