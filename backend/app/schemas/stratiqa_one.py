"""STRATIQA One — executive home & war room composite schemas."""

from __future__ import annotations

from pydantic import BaseModel

from app.schemas.goal import GoalOut
from app.schemas.project import ProjectOut
from app.schemas.recommendation import RecommendationOut


class PriorityItem(BaseModel):
    title: str
    detail: str
    severity: str  # info / warning / danger
    source: str


class RiskItem(BaseModel):
    title: str
    level: str
    context: str


class OpportunityItem(BaseModel):
    title: str
    estimated_impact: str | None
    recommendation: str | None


class ExecutiveHome(BaseModel):
    """STRATIQA One Home — intelligence before analytics."""

    welcome: str
    summary: str
    todays_priorities: list[PriorityItem]
    risks: list[RiskItem]
    opportunities: list[OpportunityItem]
    goals: list[GoalOut]
    projects: list[ProjectOut]
    recommendations: list[RecommendationOut]


class WarRoom(BaseModel):
    """Executive War Room — single-page command center."""

    critical_risks: list[RiskItem]
    goals: list[GoalOut]
    projects: list[ProjectOut]
    recommendations: list[RecommendationOut]
    opportunities: list[OpportunityItem]
    business_events: list[dict]
    twin_insights: list[str]


class AskRequest(BaseModel):
    query: str


class AskResponse(BaseModel):
    answer: str
    confidence_score: float
    data_sources: list[str]
    related_recommendations: list[RecommendationOut]
