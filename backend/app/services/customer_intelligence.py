"""Customer Intelligence service.

Turns the raw customer / health / support tables into an executive view:
per-account health, base-level stats, and grounded, explainable signals
(churn risk, support load, NPS trend). Every signal cites the data it came
from — never generic advice. Deterministic so the dashboard and tests agree.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.models.analytics import KPI
from app.models.customers import Customer, CustomerHealth, SupportTicket
from app.schemas.customers import (
    CustomerHealthOut,
    CustomerOverview,
    CustomerSignal,
    CustomerStats,
)

_AT_RISK = 60.0  # churn risk at/above this is "at risk"
_WATCH = 35.0


def _status(health_score: float | None, churn_risk: float | None) -> str:
    if churn_risk is not None and churn_risk >= _AT_RISK:
        return "at_risk"
    if (churn_risk is not None and churn_risk >= _WATCH) or (
        health_score is not None and health_score < 60
    ):
        return "watch"
    return "healthy"


def _avg(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 1) if values else None


def overview(db: DBSession, org_id: uuid.UUID) -> CustomerOverview:
    customers = list(
        db.scalars(select(Customer).where(Customer.organization_id == org_id)).all()
    )
    ids = [c.id for c in customers]

    health_by_customer: dict[uuid.UUID, CustomerHealth] = {}
    if ids:
        for h in db.scalars(
            select(CustomerHealth).where(CustomerHealth.customer_id.in_(ids))
        ).all():
            health_by_customer[h.customer_id] = h

    open_by_customer: dict[uuid.UUID, int] = {}
    if ids:
        for t in db.scalars(
            select(SupportTicket).where(
                SupportTicket.customer_id.in_(ids), SupportTicket.status == "open"
            )
        ).all():
            open_by_customer[t.customer_id] = open_by_customer.get(t.customer_id, 0) + 1

    rows: list[CustomerHealthOut] = []
    health_scores: list[float] = []
    churn_scores: list[float] = []
    for c in customers:
        h = health_by_customer.get(c.id)
        hs = float(h.health_score) if h and h.health_score is not None else None
        cr = float(h.churn_risk) if h and h.churn_risk is not None else None
        if hs is not None:
            health_scores.append(hs)
        if cr is not None:
            churn_scores.append(cr)
        rows.append(
            CustomerHealthOut(
                id=str(c.id),
                customer_name=c.customer_name,
                segment=c.segment,
                health_score=hs,
                churn_risk=cr,
                open_tickets=open_by_customer.get(c.id, 0),
                status=_status(hs, cr),
            )
        )

    # Riskiest first so the table leads with what needs attention.
    rows.sort(key=lambda r: (-(r.churn_risk or 0), r.health_score or 999))

    at_risk = [r for r in rows if r.status == "at_risk"]
    total_open = sum(open_by_customer.values())

    stats = CustomerStats(
        total_customers=len(customers),
        avg_health_score=_avg(health_scores),
        avg_churn_risk=_avg(churn_scores),
        at_risk_count=len(at_risk),
        open_tickets=total_open,
    )

    return CustomerOverview(
        stats=stats,
        customers=rows,
        signals=_signals(db, org_id, rows, at_risk, total_open),
        generated_at=datetime.utcnow(),
    )


def _signals(
    db: DBSession,
    org_id: uuid.UUID,
    rows: list[CustomerHealthOut],
    at_risk: list[CustomerHealthOut],
    open_tickets: int,
) -> list[CustomerSignal]:
    out: list[CustomerSignal] = []

    if not rows:
        return [
            CustomerSignal(
                title="No customer signals yet",
                finding="Add customers, health scores, and support data to activate "
                "retention intelligence.",
                severity="info",
                confidence_score=55.0,
                data_sources=["customers"],
            )
        ]

    if at_risk:
        names = ", ".join(r.customer_name for r in at_risk[:3])
        more = f" (+{len(at_risk) - 3} more)" if len(at_risk) > 3 else ""
        out.append(
            CustomerSignal(
                title=f"{len(at_risk)} account(s) at churn risk",
                finding=f"{len(at_risk)} of {len(rows)} customers show churn risk "
                f"≥ {_AT_RISK:.0f}%: {names}{more}.",
                severity="danger" if len(at_risk) >= 2 else "warning",
                confidence_score=78.0,
                data_sources=["customers + customer_health"],
                recommended_action="Trigger executive save-plays on the at-risk accounts.",
            )
        )

    if open_tickets:
        loaded = [r for r in rows if r.open_tickets > 0]
        worst = max(loaded, key=lambda r: r.open_tickets) if loaded else None
        finding = f"{open_tickets} support ticket(s) are open across {len(loaded)} account(s)."
        if worst:
            finding += f" '{worst.customer_name}' carries the most ({worst.open_tickets})."
        out.append(
            CustomerSignal(
                title=f"{open_tickets} open support ticket(s)",
                finding=finding,
                severity="warning" if open_tickets >= 3 else "info",
                confidence_score=70.0,
                data_sources=["support_tickets"],
                recommended_action="Prioritize tickets on at-risk accounts first."
                if at_risk
                else None,
            )
        )

    nps = list(
        db.scalars(
            select(KPI)
            .where(KPI.organization_id == org_id, KPI.kpi_name == "NPS")
            .order_by(KPI.recorded_at.desc())
        ).all()
    )
    if len(nps) >= 2 and nps[0].value is not None and nps[1].value is not None:
        latest, prev = float(nps[0].value), float(nps[1].value)
        delta = latest - prev
        improving = delta > 0
        out.append(
            CustomerSignal(
                title=f"NPS {latest:.0f} ({delta:+.0f} pts)",
                finding=f"NPS {'rose' if improving else 'fell' if delta else 'held'} "
                f"{abs(delta):.0f} points to {latest:.0f} vs. the prior reading.",
                severity="success" if improving else "warning" if delta else "info",
                confidence_score=74.0,
                data_sources=["kpis (NPS)"],
            )
        )

    if not out:
        out.append(
            CustomerSignal(
                title="Customer base is healthy",
                finding=f"All {len(rows)} tracked account(s) are below the churn-risk "
                "threshold with no open tickets.",
                severity="success",
                confidence_score=72.0,
                data_sources=["customers + customer_health"],
            )
        )
    return out
