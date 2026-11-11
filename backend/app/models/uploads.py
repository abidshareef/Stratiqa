"""Data ingestion: uploaded business files (sales reports, exports, docs).

A ``DataUpload`` is the raw record of a file a user submitted. Tabular files
(CSV/Excel, or tables extracted from PDF/Word) are parsed into a column preview
and later *committed* — mapped into real entities (KPIs, customers, products).
Prose/image files are stored with extracted text (or none) for reference.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, UUIDPk
from app.models._types import JSONB, fk, fk_optional


class DataUpload(Base):
    __tablename__ = "data_uploads"

    id: Mapped[UUIDPk]
    organization_id = fk("organizations.id")
    uploaded_by = fk_optional("users.id")

    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(120))
    #: csv | excel | pdf | word | image | unknown
    file_kind: Mapped[str] = mapped_column(String(20), default="unknown", nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    #: parsed | text_only | manual_required | committed | failed
    status: Mapped[str] = mapped_column(String(24), default="parsed", nullable=False)
    storage_path: Mapped[str | None] = mapped_column(String(500))

    columns: Mapped[list] = mapped_column(JSONB, default=list)
    preview_rows: Mapped[list] = mapped_column(JSONB, default=list)
    row_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    extracted_text: Mapped[str | None] = mapped_column(Text)
    suggested_mapping: Mapped[dict] = mapped_column(JSONB, default=dict)
    commit_summary: Mapped[dict] = mapped_column(JSONB, default=dict)
    error: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
