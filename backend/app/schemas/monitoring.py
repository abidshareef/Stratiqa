"""Alert & Monitoring schemas — a cross-cutting live alert feed + incidents."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AlertItem(BaseModel):
    """A single alert — either derived live from business data or persisted."""

    title: str
    detail: str
    severity: str  # info | warning | danger
    category: str  # risk | customer | inventory | kpi | goal | delivery | system
    source: str  # the data it came from
    status: str  # open | resolved
    at: datetime | None = None
    derived: bool  # True = computed live from business data, False = stored


class IncidentOut(BaseModel):
    id: str
    incident_type: str
    description: str | None
    resolved: bool


class MonitoringStats(BaseModel):
    total_open: int
    critical: int  # severity == danger
    warning: int
    incidents_open: int
    anomalies: int


class MonitoringOverview(BaseModel):
    stats: MonitoringStats
    alerts: list[AlertItem]
    incidents: list[IncidentOut]
    generated_at: datetime
