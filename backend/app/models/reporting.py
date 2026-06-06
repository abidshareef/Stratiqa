"""Section 14: Reporting Engine."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, UUIDPk
from app.models._types import fk, fk_optional


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[UUIDPk]
    organization_id = fk("organizations.id")
    report_type: Mapped[str] = mapped_column(String(40), nullable=False)  # daily/weekly/...
    title: Mapped[str | None] = mapped_column(String(255))
    content: Mapped[dict] = mapped_column(JSONB, default=dict)  # structured report body
    generated_by = fk_optional("users.id")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ReportAsset(Base):
    __tablename__ = "report_assets"

    id: Mapped[UUIDPk]
    report_id = fk("reports.id")
    asset_type: Mapped[str] = mapped_column(String(40), nullable=False)  # chart/graph/image/pdf
    asset_url: Mapped[str | None] = mapped_column(Text)


class ExecutiveBrief(Base):
    __tablename__ = "executive_briefs"

    id: Mapped[UUIDPk]
    organization_id = fk("organizations.id")
    brief_type: Mapped[str] = mapped_column(String(40), nullable=False)  # morning/evening/...
    content: Mapped[dict] = mapped_column(JSONB, default=dict)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
