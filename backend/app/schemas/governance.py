"""Audit & Governance schemas (Section 16).

Two complementary lenses on accountability:

* **Audit trail** — an immutable, human-readable log of security- and
  data-relevant actions (who did what, when, from where).
* **Decision governance** — how explainable the platform's AI recommendations
  are, measured against the spec's mandate that every recommendation carry
  reasoning, a confidence score, and named data sources.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AuditEntry(BaseModel):
    """One recorded action in the audit trail."""

    id: str
    action: str  # e.g. user.login, user.login.failed, data.commit
    category: str  # security | data | other
    actor: str  # display name / email, or "system"
    resource: str | None = None
    detail: str | None = None
    ip_address: str | None = None
    at: datetime | None = None


class GovernanceStats(BaseModel):
    total_events: int
    security_events: int
    failed_logins: int
    data_events: int


class DecisionGovernance(BaseModel):
    """Explainability coverage across the org's AI recommendations."""

    total_decisions: int
    with_reasoning: int
    with_confidence: int
    with_data_sources: int
    #: % of decisions that carry reasoning, confidence, AND data sources.
    explainability_coverage: float
    avg_confidence: float


class GovernanceOverview(BaseModel):
    stats: GovernanceStats
    decisions: DecisionGovernance
    trail: list[AuditEntry]
    generated_at: datetime
