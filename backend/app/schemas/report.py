"""Report & executive brief schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from app.schemas.common import ORMModel


class ReportOut(ORMModel):
    id: uuid.UUID
    report_type: str
    title: str | None
    content: dict
    created_at: datetime


class ReportSummary(ORMModel):
    id: uuid.UUID
    report_type: str
    title: str | None
    created_at: datetime


class BriefOut(ORMModel):
    id: uuid.UUID
    brief_type: str
    content: dict
    generated_at: datetime
