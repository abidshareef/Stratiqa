"""Audit & Governance service (Section 16).

Builds the org's accountability overview from data the platform already
records: the ``audit_logs`` trail (written by auth and data-ingestion flows)
and the explainability fields every ``Recommendation`` carries. Nothing here is
speculative — it reports what is actually logged and how well the AI decisions
meet the spec's explainability bar.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.models.governance import AuditLog
from app.models.identity import User
from app.models.recommendations import Recommendation
from app.schemas.governance import (
    AuditEntry,
    DecisionGovernance,
    GovernanceOverview,
    GovernanceStats,
)

_TRAIL_LIMIT = 100

# Action prefixes → audit category. Anything unmatched falls back to "other".
_SECURITY_PREFIXES = ("user.login", "user.logout", "user.mfa", "user.register", "auth.")
_DATA_PREFIXES = ("data.", "upload.", "ingestion.")


def _categorize(action: str) -> str:
    if action.startswith(_SECURITY_PREFIXES):
        return "security"
    if action.startswith(_DATA_PREFIXES):
        return "data"
    return "other"


def _actor_names(db: DBSession, user_ids: set[uuid.UUID]) -> dict[uuid.UUID, str]:
    if not user_ids:
        return {}
    rows = db.execute(
        select(User.id, User.full_name, User.email).where(User.id.in_(user_ids))
    ).all()
    return {uid: (name or email) for uid, name, email in rows}


def _decision_governance(db: DBSession, org_id: uuid.UUID) -> DecisionGovernance:
    recs = db.scalars(
        select(Recommendation).where(Recommendation.organization_id == org_id)
    ).all()
    total = len(recs)
    if total == 0:
        return DecisionGovernance(
            total_decisions=0,
            with_reasoning=0,
            with_confidence=0,
            with_data_sources=0,
            explainability_coverage=0.0,
            avg_confidence=0.0,
        )

    with_reasoning = sum(1 for r in recs if (r.reasoning or "").strip())
    with_confidence = sum(1 for r in recs if r.confidence_score and float(r.confidence_score) > 0)
    with_sources = sum(1 for r in recs if (r.data_sources or "").strip())
    fully_explained = sum(
        1
        for r in recs
        if (r.reasoning or "").strip()
        and r.confidence_score
        and float(r.confidence_score) > 0
        and (r.data_sources or "").strip()
    )
    avg_conf = sum(float(r.confidence_score or 0) for r in recs) / total

    return DecisionGovernance(
        total_decisions=total,
        with_reasoning=with_reasoning,
        with_confidence=with_confidence,
        with_data_sources=with_sources,
        explainability_coverage=round(fully_explained / total * 100, 1),
        avg_confidence=round(avg_conf, 1),
    )


def overview(db: DBSession, org_id: uuid.UUID) -> GovernanceOverview:
    logs = db.scalars(
        select(AuditLog)
        .where(AuditLog.organization_id == org_id)
        .order_by(AuditLog.timestamp.desc())
        .limit(_TRAIL_LIMIT)
    ).all()

    names = _actor_names(db, {log.user_id for log in logs if log.user_id})

    trail: list[AuditEntry] = []
    security = failed = data = 0
    for log in logs:
        category = _categorize(log.action)
        if category == "security":
            security += 1
        elif category == "data":
            data += 1
        if log.action.endswith(".failed"):
            failed += 1
        trail.append(
            AuditEntry(
                id=str(log.id),
                action=log.action,
                category=category,
                actor=names.get(log.user_id, "system") if log.user_id else "system",
                resource=log.resource,
                detail=log.detail,
                ip_address=log.ip_address,
                at=log.timestamp,
            )
        )

    stats = GovernanceStats(
        total_events=len(logs),
        security_events=security,
        failed_logins=failed,
        data_events=data,
    )

    return GovernanceOverview(
        stats=stats,
        decisions=_decision_governance(db, org_id),
        trail=trail,
        generated_at=datetime.utcnow(),
    )
