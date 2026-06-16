"""Schemas for the data-ingestion (file upload) flow."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel

#: Entities a tabular upload can be committed into.
IngestTarget = Literal["kpi", "customers", "products"]


class UploadOut(ORMModel):
    id: uuid.UUID
    filename: str
    file_kind: str
    status: str
    row_count: int
    columns: list[str]
    created_at: datetime


class UploadDetail(UploadOut):
    preview_rows: list[dict]
    extracted_text: str | None
    suggested_mapping: dict
    commit_summary: dict
    error: str | None


class CommitMapping(BaseModel):
    """How the user maps the file's columns onto a target entity.

    ``fields`` maps a canonical field name to the source column header, e.g.
    ``{"value": "Net Revenue", "date": "Month"}`` for a KPI import.
    """

    target: IngestTarget
    fields: dict[str, str] = Field(default_factory=dict)
    #: Constant KPI label when the metric name is not itself a column.
    kpi_label: str | None = None


class AnalysisChanges(BaseModel):
    """How newly ingested data shifted the recommendation analysis.

    ``new_insights`` / ``resolved_insights`` are recommendation titles that
    appeared or disappeared versus the analysis before this commit, letting the
    user recognize the change instead of just trusting a refresh count.
    """

    new_insights: list[str] = Field(default_factory=list)
    resolved_insights: list[str] = Field(default_factory=list)
    unchanged: int = 0


class CommitResult(BaseModel):
    upload_id: uuid.UUID
    target: str
    created: dict[str, int]
    skipped: int
    total: int
    recommendations_refreshed: int
    analysis_changes: AnalysisChanges
