"""Customer Intelligence schemas — health, churn, support, grounded signals."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class CustomerHealthOut(BaseModel):
    """One customer with its derived health picture."""

    id: str
    customer_name: str
    segment: str | None
    health_score: float | None
    churn_risk: float | None
    open_tickets: int
    status: str  # healthy | watch | at_risk


class CustomerStats(BaseModel):
    total_customers: int
    avg_health_score: float | None
    avg_churn_risk: float | None
    at_risk_count: int
    open_tickets: int


class CustomerSignal(BaseModel):
    """A grounded, explainable finding about the customer base."""

    title: str
    finding: str
    severity: str  # info | warning | danger | success
    confidence_score: float
    data_sources: list[str]
    recommended_action: str | None = None


class CustomerOverview(BaseModel):
    stats: CustomerStats
    customers: list[CustomerHealthOut]
    signals: list[CustomerSignal]
    generated_at: datetime
