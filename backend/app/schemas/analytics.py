"""Analytics overview schemas — powers the executive dashboard charts."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class KpiCard(BaseModel):
    key: str
    label: str
    value: float
    unit: str  # "$", "%", "mo", "" ...
    fmt: str  # currency | percent | number
    delta_pct: float | None  # change vs previous reading
    direction: str  # up | down | flat
    positive: bool  # whether the movement is good for the business
    series: list[float]  # chronological values for the sparkline


class TimeSeries(BaseModel):
    labels: list[str]
    values: list[float]


class GoalProgressOut(BaseModel):
    title: str
    progress: float
    target_date: str | None
    status: str
    series: list[float]


class ProjectHealthOut(BaseModel):
    name: str
    score: int
    label: str  # healthy | at_risk | critical
    open_risks: int
    overdue_tasks: int


class AnalyticsOverview(BaseModel):
    kpis: list[KpiCard]
    revenue_trend: TimeSeries
    goal_progress: list[GoalProgressOut]
    project_health: list[ProjectHealthOut]
    generated_at: datetime
