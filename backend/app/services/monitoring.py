"""Alert & Monitoring service.

The most cross-cutting view in the platform: a single live alert feed that
scans every domain — project risk, customer churn, inventory, KPI trend, goal
slippage, delivery — and folds in persisted alerts, anomalies, and incidents.
Derived alerts are computed deterministically from the same data the rest of
the app reasons over, so nothing here is speculative or generic.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.models.analytics import KPI, Anomaly
from app.models.customers import Customer, CustomerHealth
from app.models.goals import GoalProgress, StrategicGoal
from app.models.monitoring import Alert, Incident
from app.models.products import Inventory, Product
from app.models.projects import Project, ProjectRisk, Task
from app.schemas.monitoring import (
    AlertItem,
    IncidentOut,
    MonitoringOverview,
    MonitoringStats,
)

_SEVERITY_RANK = {"danger": 3, "warning": 2, "info": 1}


def _derived_alerts(db: DBSession, org_id: uuid.UUID) -> list[AlertItem]:
    out: list[AlertItem] = []
    today = date.today()

    # --- Risk: open high/critical project risks ---
    for risk, pname in db.execute(
        select(ProjectRisk, Project.name)
        .join(Project, Project.id == ProjectRisk.project_id)
        .where(
            Project.organization_id == org_id,
            ProjectRisk.risk_level.in_(["high", "critical"]),
        )
    ).all():
        unmitigated = not (risk.mitigation and risk.mitigation.strip())
        out.append(
            AlertItem(
                title=f"{risk.risk_level.title()} risk: {risk.risk_title}",
                detail=f"On '{pname}'. {risk.impact or ''}".strip()
                + (" No mitigation recorded." if unmitigated else ""),
                severity="danger" if risk.risk_level == "critical" else "warning",
                category="risk",
                source="project_risks",
                status="open",
                derived=True,
            )
        )

    # --- Customer: accounts at churn risk ---
    customers = {
        c.id: c.customer_name
        for c in db.scalars(select(Customer).where(Customer.organization_id == org_id)).all()
    }
    if customers:
        for h in db.scalars(
            select(CustomerHealth).where(CustomerHealth.customer_id.in_(list(customers)))
        ).all():
            if h.churn_risk is not None and float(h.churn_risk) >= 60:
                churn = float(h.churn_risk)
                out.append(
                    AlertItem(
                        title=f"Churn risk: {customers[h.customer_id]}",
                        detail=f"Churn risk at {churn:.0f}% — above the 60% threshold.",
                        severity="danger" if churn >= 70 else "warning",
                        category="customer",
                        source="customer_health",
                        status="open",
                        derived=True,
                    )
                )

    # --- Inventory: SKUs at/below reorder level ---
    products = {
        p.id: p.product_name
        for p in db.scalars(select(Product).where(Product.organization_id == org_id)).all()
    }
    if products:
        for inv in db.scalars(
            select(Inventory).where(Inventory.product_id.in_(list(products)))
        ).all():
            if inv.quantity <= inv.reorder_level:
                out.append(
                    AlertItem(
                        title=f"Low stock: {products[inv.product_id]}",
                        detail=f"On hand {inv.quantity} ≤ reorder level {inv.reorder_level}.",
                        severity="danger" if inv.quantity <= 0 else "warning",
                        category="inventory",
                        source="inventory",
                        status="open",
                        derived=True,
                    )
                )

    # --- KPI: monthly revenue decline ---
    revenue = list(
        db.scalars(
            select(KPI)
            .where(KPI.organization_id == org_id, KPI.kpi_name == "Monthly Revenue")
            .order_by(KPI.recorded_at.desc())
        ).all()
    )
    if len(revenue) >= 2 and revenue[0].value is not None and revenue[1].value is not None:
        latest, prev = float(revenue[0].value), float(revenue[1].value)
        if prev and latest < prev:
            drop = (prev - latest) / prev * 100
            out.append(
                AlertItem(
                    title=f"Monthly Revenue down {drop:.0f}%",
                    detail=f"Latest reading ${latest:,.0f} vs. ${prev:,.0f} prior.",
                    severity="danger" if drop >= 15 else "warning",
                    category="kpi",
                    source="kpis (Monthly Revenue)",
                    status="open",
                    derived=True,
                )
            )

    # --- Goals: slipping toward the target date ---
    for g in db.scalars(
        select(StrategicGoal).where(
            StrategicGoal.organization_id == org_id, StrategicGoal.status == "active"
        )
    ).all():
        latest = db.scalar(
            select(GoalProgress)
            .where(GoalProgress.goal_id == g.id)
            .order_by(GoalProgress.recorded_at.desc())
        )
        prog = float(latest.progress_percentage) if latest else 0.0
        if g.target_date and prog < 50 and 0 <= (g.target_date - today).days <= 60:
            out.append(
                AlertItem(
                    title=f"Goal slipping: {g.title}",
                    detail=f"At {prog:.0f}% with {(g.target_date - today).days} day(s) "
                    "to target.",
                    severity="warning",
                    category="goal",
                    source="strategic_goals + goal_progress",
                    status="open",
                    derived=True,
                )
            )

    # --- Delivery: cluster of overdue tasks ---
    overdue = len(
        db.scalars(
            select(Task)
            .join(Project, Project.id == Task.project_id)
            .where(
                Project.organization_id == org_id,
                Task.due_date < today,
                Task.status != "done",
            )
        ).all()
    )
    if overdue >= 3:
        out.append(
            AlertItem(
                title=f"{overdue} overdue tasks",
                detail="A cluster of overdue tasks may signal an under-resourced delivery.",
                severity="warning",
                category="delivery",
                source="tasks",
                status="open",
                derived=True,
            )
        )

    return out


def _persisted_alerts(db: DBSession, org_id: uuid.UUID) -> list[AlertItem]:
    out: list[AlertItem] = []
    for a in db.scalars(select(Alert).where(Alert.organization_id == org_id)).all():
        sev = a.severity if a.severity in _SEVERITY_RANK else "info"
        out.append(
            AlertItem(
                title=a.title,
                detail=f"System alert ({a.status}).",
                severity=sev,
                category="system",
                source="alerts",
                status=a.status,
                at=a.created_at,
                derived=False,
            )
        )
    for an in db.scalars(select(Anomaly).where(Anomaly.organization_id == org_id)).all():
        sev = "danger" if an.severity in {"high", "critical"} else "warning"
        out.append(
            AlertItem(
                title=f"Anomaly: {an.anomaly_type}",
                detail=an.description or "Anomaly detected.",
                severity=sev,
                category="system",
                source="anomalies",
                status="open",
                at=an.detected_at,
                derived=False,
            )
        )
    return out


def overview(db: DBSession, org_id: uuid.UUID) -> MonitoringOverview:
    derived = _derived_alerts(db, org_id)
    persisted = _persisted_alerts(db, org_id)
    alerts = derived + persisted

    # Most severe first; within a severity, derived business alerts lead.
    alerts.sort(key=lambda a: (-_SEVERITY_RANK.get(a.severity, 0), not a.derived))

    open_alerts = [a for a in alerts if a.status == "open"]
    incidents = list(
        db.scalars(select(Incident).where(Incident.organization_id == org_id)).all()
    )
    anomaly_count = len(
        db.scalars(select(Anomaly).where(Anomaly.organization_id == org_id)).all()
    )

    stats = MonitoringStats(
        total_open=len(open_alerts),
        critical=sum(1 for a in open_alerts if a.severity == "danger"),
        warning=sum(1 for a in open_alerts if a.severity == "warning"),
        incidents_open=sum(1 for i in incidents if not i.resolved),
        anomalies=anomaly_count,
    )

    return MonitoringOverview(
        stats=stats,
        alerts=alerts,
        incidents=[
            IncidentOut(
                id=str(i.id),
                incident_type=i.incident_type,
                description=i.description,
                resolved=i.resolved,
            )
            for i in incidents
        ],
        generated_at=datetime.utcnow(),
    )


def top_open_alerts(db: DBSession, org_id: uuid.UUID, limit: int = 5) -> list[AlertItem]:
    """The most severe open alerts — used by the War Room activity stream."""
    return [a for a in overview(db, org_id).alerts if a.status == "open"][:limit]
