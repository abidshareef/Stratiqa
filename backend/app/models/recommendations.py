"""Section 11: Recommendations & Learning."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, UUIDPk
from app.models._types import fk


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[UUIDPk]
    organization_id = fk("organizations.id")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    reasoning: Mapped[str | None] = mapped_column(Text)
    confidence_score: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    expected_impact: Mapped[str | None] = mapped_column(Text)
    risk_level: Mapped[str] = mapped_column(String(20), default="low", nullable=False)
    data_sources: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class RecommendationFeedback(Base):
    __tablename__ = "recommendation_feedback"

    id: Mapped[UUIDPk]
    recommendation_id = fk("recommendations.id")
    accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    feedback: Mapped[str | None] = mapped_column(Text)


class OutcomeTracking(Base):
    __tablename__ = "outcome_tracking"

    id: Mapped[UUIDPk]
    recommendation_id = fk("recommendations.id")
    actual_outcome: Mapped[str | None] = mapped_column(Text)
    success_rating: Mapped[int | None] = mapped_column(Integer)


class LearningEvent(Base):
    __tablename__ = "learning_events"

    id: Mapped[UUIDPk]
    organization_id = fk("organizations.id")
    event_summary: Mapped[str] = mapped_column(Text, nullable=False)
    learning_type: Mapped[str | None] = mapped_column(String(60))
