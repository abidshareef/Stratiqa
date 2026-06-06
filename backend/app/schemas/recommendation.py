"""Recommendation schemas — always carry explainability fields."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMModel


class RecommendationOut(ORMModel):
    id: uuid.UUID
    title: str
    description: str | None
    reasoning: str | None
    confidence_score: float
    expected_impact: str | None
    risk_level: str
    data_sources: str | None
    status: str
    created_at: datetime


class FeedbackIn(BaseModel):
    accepted: bool
    feedback: str | None = None
