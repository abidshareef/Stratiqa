"""AI Agent layer schemas — specialist agents + their grounded insights."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AgentInsight(BaseModel):
    """A single grounded finding from a specialist agent. Carries the
    explainability contract: what, why it matters, confidence, and sources."""

    agent_type: str
    title: str
    finding: str
    severity: str  # info | warning | danger | success
    confidence_score: float
    data_sources: list[str]
    metric: str | None = None
    recommended_action: str | None = None


class AgentSummary(BaseModel):
    agent_type: str
    name: str
    domain: str
    status: str
    headline: str
    insight_count: int
    top_severity: str


class AgentDetail(BaseModel):
    agent_type: str
    name: str
    domain: str
    status: str
    insights: list[AgentInsight]


class AgentRoster(BaseModel):
    agents: list[AgentSummary]
    generated_at: datetime


class AgentAskRequest(BaseModel):
    query: str


class AgentAskResponse(BaseModel):
    agent_type: str
    name: str
    answer: str
    confidence_score: float
    data_sources: list[str]
    insights: list[AgentInsight]
