"""AI Agent Layer.

A roster of specialist agents (Finance, Revenue, Delivery, Risk, Customer,
Product, People) plus the STRATIQA One master. Each agent reasons over its own
domain data and emits grounded, explainable insights — never generic advice.
The same deterministic data layer the dashboard uses is the source of truth; an
LLM gateway can later phrase the narrative on top of these facts.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.models.agents import Agent, AgentInteraction
from app.models.analytics import KPI, Opportunity
from app.models.customers import Customer, CustomerHealth, SupportTicket
from app.models.discovery import BusinessProfile
from app.models.goals import GoalProgress, StrategicGoal
from app.models.products import Inventory, Product, ProductMetric
from app.models.projects import Project, ProjectRisk, Task
from app.models.recommendations import Recommendation
from app.schemas.agents import (
    AgentAskResponse,
    AgentDetail,
    AgentInsight,
    AgentRoster,
    AgentSummary,
)

# Agent registry: type -> (display name, domain).
AGENT_DEFS: dict[str, tuple[str, str]] = {
    "STRATIQA_ONE": ("STRATIQA One", "Master orchestrator — synthesizes every domain"),
    "FINANCE": ("Finance Agent", "Revenue, margin, burn & runway"),
    "SALES": ("Revenue Agent", "Customers, CAC & pipeline"),
    "PROJECT": ("Delivery Agent", "Project health & execution"),
    "RISK": ("Risk Agent", "Threats across the portfolio"),
    "CUSTOMER_SUCCESS": ("Customer Agent", "Retention, NPS & support"),
    "PRODUCT": ("Product Agent", "Catalog, inventory & demand"),
    "HR": ("People Agent", "Headcount & capacity"),
}

_SEVERITY_RANK = {"danger": 3, "warning": 2, "success": 1, "info": 0}


def ensure_agents(db: DBSession, org_id: uuid.UUID) -> list[Agent]:
    """Register the specialist agents for an org (idempotent)."""
    existing = {
        a.agent_type: a
        for a in db.scalars(select(Agent).where(Agent.organization_id == org_id)).all()
    }
    created = False
    for agent_type, (name, _domain) in AGENT_DEFS.items():
        if agent_type not in existing:
            agent = Agent(
                organization_id=org_id, name=name, agent_type=agent_type, status="active"
            )
            db.add(agent)
            existing[agent_type] = agent
            created = True
    if created:
        db.flush()
    return [existing[t] for t in AGENT_DEFS if t in existing]


# --- KPI helpers -------------------------------------------------------------

def _kpi_readings(db: DBSession, org_id: uuid.UUID, name: str) -> list[KPI]:
    return list(
        db.scalars(
            select(KPI)
            .where(KPI.organization_id == org_id, KPI.kpi_name == name)
            .order_by(KPI.recorded_at.desc())
        ).all()
    )


def _pct(latest: float, prev: float) -> float:
    return (latest - prev) / abs(prev) * 100 if prev else 0.0


def _insight(
    agent_type: str,
    title: str,
    finding: str,
    severity: str,
    confidence: float,
    sources: list[str],
    *,
    metric: str | None = None,
    action: str | None = None,
) -> AgentInsight:
    return AgentInsight(
        agent_type=agent_type,
        title=title,
        finding=finding,
        severity=severity,
        confidence_score=confidence,
        data_sources=sources,
        metric=metric,
        recommended_action=action,
    )


def _trend_insight(
    db: DBSession,
    org_id: uuid.UUID,
    agent_type: str,
    kpi_name: str,
    *,
    lower_is_better: bool = False,
    unit: str = "",
) -> AgentInsight | None:
    rows = _kpi_readings(db, org_id, kpi_name)
    if not rows or rows[0].value is None:
        return None
    latest = float(rows[0].value)
    metric = f"{latest:,.0f}{unit}"
    if len(rows) < 2 or rows[1].value is None:
        return _insight(
            agent_type, f"{kpi_name}: {metric}",
            f"Latest {kpi_name} is {metric}. Not enough history yet for a trend.",
            "info", 60.0, [f"kpis ({kpi_name})"], metric=metric,
        )
    change = _pct(latest, float(rows[1].value))
    improving = (change < 0) if lower_is_better else (change > 0)
    if abs(change) < 0.5:
        sev = "info"
    elif improving:
        sev = "success"
    else:
        sev = "danger" if abs(change) >= 15 else "warning"
    word = "rose" if change > 0 else "fell" if change < 0 else "held"
    finding = f"{kpi_name} {word} {abs(change):.1f}% to {metric} vs. the prior reading."
    return _insight(
        agent_type, f"{kpi_name} {change:+.1f}%", finding, sev,
        76.0, [f"kpis ({kpi_name})"], metric=metric,
    )


# --- Per-agent insight generators -------------------------------------------

def _finance(db: DBSession, org_id: uuid.UUID) -> list[AgentInsight]:
    out: list[AgentInsight] = []
    for name, lower, unit in [
        ("Monthly Revenue", False, ""),
        ("Gross Margin", False, "%"),
        ("Net Burn", True, ""),
    ]:
        ins = _trend_insight(db, org_id, "FINANCE", name, lower_is_better=lower, unit=unit)
        if ins:
            out.append(ins)
    runway = _kpi_readings(db, org_id, "Cash Runway")
    if runway and runway[0].value is not None:
        months = float(runway[0].value)
        sev = "danger" if months < 6 else "warning" if months < 12 else "success"
        out.append(
            _insight(
                "FINANCE", f"Cash runway: {months:.0f} months",
                f"At the current burn the company has ~{months:.0f} months of runway.",
                sev, 80.0, ["kpis (Cash Runway)"], metric=f"{months:.0f}mo",
                action="Plan the next raise 9-12 months out." if months < 12 else None,
            )
        )
    return out


def _sales(db: DBSession, org_id: uuid.UUID) -> list[AgentInsight]:
    out: list[AgentInsight] = []
    for name, lower, unit in [("Active Customers", False, ""), ("CAC", True, "")]:
        ins = _trend_insight(db, org_id, "SALES", name, lower_is_better=lower, unit=unit)
        if ins:
            out.append(ins)
    opps = list(
        db.scalars(select(Opportunity).where(Opportunity.organization_id == org_id)).all()
    )
    if opps:
        top = "; ".join(o.title for o in opps[:3])
        out.append(
            _insight(
                "SALES", f"{len(opps)} growth opportunit{'y' if len(opps) == 1 else 'ies'} open",
                f"Pipeline of expansion plays: {top}.", "success", 70.0,
                ["opportunities"], action="Prioritize by estimated impact.",
            )
        )
    return out


def _project(db: DBSession, org_id: uuid.UUID) -> list[AgentInsight]:
    today = date.today()
    out: list[AgentInsight] = []
    projects = list(
        db.scalars(
            select(Project).where(
                Project.organization_id == org_id, Project.status != "completed"
            )
        ).all()
    )
    for p in projects:
        risks = list(db.scalars(select(ProjectRisk).where(ProjectRisk.project_id == p.id)).all())
        open_high = sum(1 for r in risks if r.risk_level in {"high", "critical"})
        tasks = list(db.scalars(select(Task).where(Task.project_id == p.id)).all())
        overdue = sum(1 for t in tasks if t.due_date and t.due_date < today and t.status != "done")
        score = max(0, min(100, 100 - open_high * 20 - overdue * 6))
        if score >= 75:
            continue  # healthy projects don't need an alert
        sev = "danger" if score < 45 else "warning"
        out.append(
            _insight(
                "PROJECT", f"'{p.name}' health {score}/100",
                f"'{p.name}' has {open_high} high/critical risk(s) and {overdue} overdue task(s).",
                sev, 78.0, [f"projects + tasks + project_risks (project_id={p.id})"],
                metric=f"{score}/100",
                action="Re-sequence the critical path and assign owners to open risks.",
            )
        )
    if projects and not out:
        out.append(
            _insight(
                "PROJECT", "All active projects healthy",
                f"All {len(projects)} active project(s) score 75+ on delivery health.",
                "success", 72.0, ["projects + tasks + project_risks"],
            )
        )
    return out


def _risk(db: DBSession, org_id: uuid.UUID) -> list[AgentInsight]:
    rows = db.execute(
        select(ProjectRisk, Project.name)
        .join(Project, Project.id == ProjectRisk.project_id)
        .where(
            Project.organization_id == org_id,
            ProjectRisk.risk_level.in_(["high", "critical"]),
        )
    ).all()
    if not rows:
        return [
            _insight(
                "RISK", "No elevated risks", "No high or critical risks are currently open.",
                "success", 70.0, ["project_risks"],
            )
        ]
    out: list[AgentInsight] = []
    for risk, pname in rows:
        unmitigated = not (risk.mitigation and risk.mitigation.strip())
        sev = "danger" if risk.risk_level == "critical" else "warning"
        out.append(
            _insight(
                "RISK", f"{risk.risk_level.title()} risk on '{pname}'",
                f"{risk.risk_title}. {risk.impact or ''}".strip()
                + (" No mitigation recorded." if unmitigated else ""),
                sev, 82.0, [f"project_risks (project={pname})"],
                action="Record a mitigation owner and date." if unmitigated else None,
            )
        )
    return out


def _customer(db: DBSession, org_id: uuid.UUID) -> list[AgentInsight]:
    out: list[AgentInsight] = []
    nps = _trend_insight(db, org_id, "CUSTOMER_SUCCESS", "NPS")
    if nps:
        out.append(nps)
    customers = list(db.scalars(select(Customer).where(Customer.organization_id == org_id)).all())
    if customers:
        ids = [c.id for c in customers]
        churn_rows = list(
            db.scalars(select(CustomerHealth).where(CustomerHealth.customer_id.in_(ids))).all()
        )
        at_risk = [h for h in churn_rows if h.churn_risk is not None and float(h.churn_risk) >= 60]
        if at_risk:
            out.append(
                _insight(
                    "CUSTOMER_SUCCESS", f"{len(at_risk)} account(s) at churn risk",
                    f"{len(at_risk)} of {len(customers)} customers show churn risk ≥ 60%.",
                    "danger" if len(at_risk) >= 2 else "warning", 75.0,
                    ["customers + customer_health"],
                    action="Trigger save-plays on at-risk accounts.",
                )
            )
        open_tickets = db.scalar(
            select(SupportTicket).where(
                SupportTicket.customer_id.in_(ids), SupportTicket.status == "open"
            )
        )
        if open_tickets is not None:
            count = len(
                list(
                    db.scalars(
                        select(SupportTicket).where(
                            SupportTicket.customer_id.in_(ids),
                            SupportTicket.status == "open",
                        )
                    ).all()
                )
            )
            out.append(
                _insight(
                    "CUSTOMER_SUCCESS", f"{count} open support ticket(s)",
                    f"{count} support ticket(s) are currently open across the base.",
                    "warning" if count else "info", 68.0, ["support_tickets"],
                )
            )
    if not out:
        out.append(
            _insight(
                "CUSTOMER_SUCCESS", "No customer signals yet",
                "Add customers, NPS, and support data to activate retention intelligence.",
                "info", 55.0, ["customers"],
            )
        )
    return out


def _product(db: DBSession, org_id: uuid.UUID) -> list[AgentInsight]:
    products = list(db.scalars(select(Product).where(Product.organization_id == org_id)).all())
    if not products:
        return [
            _insight(
                "PRODUCT", "No product catalog yet",
                "Add products and inventory to unlock demand and stock intelligence.",
                "info", 55.0, ["products"],
            )
        ]
    out: list[AgentInsight] = []
    pids = [p.id for p in products]
    low_stock = [
        inv
        for inv in db.scalars(select(Inventory).where(Inventory.product_id.in_(pids))).all()
        if inv.quantity <= inv.reorder_level
    ]
    if low_stock:
        out.append(
            _insight(
                "PRODUCT", f"{len(low_stock)} SKU(s) at/below reorder level",
                f"{len(low_stock)} product(s) need restocking to avoid stockouts.",
                "warning", 74.0, ["inventory"], action="Raise purchase orders for low-stock SKUs.",
            )
        )
    metrics = list(
        db.scalars(select(ProductMetric).where(ProductMetric.product_id.in_(pids))).all()
    )
    top = max(
        (m for m in metrics if m.revenue is not None),
        key=lambda m: float(m.revenue),
        default=None,
    )
    if top is not None:
        name = next((p.product_name for p in products if p.id == top.product_id), "a product")
        out.append(
            _insight(
                "PRODUCT", f"Top product: {name}",
                f"'{name}' leads on revenue (${float(top.revenue):,.0f}).",
                "success", 70.0, ["product_metrics"], metric=f"${float(top.revenue):,.0f}",
            )
        )
    if not out:
        out.append(
            _insight(
                "PRODUCT", f"{len(products)} product(s) tracked",
                f"Catalog has {len(products)} product(s); no stock or revenue alerts.",
                "info", 60.0, ["products"],
            )
        )
    return out


def _hr(db: DBSession, org_id: uuid.UUID) -> list[AgentInsight]:
    profile = db.scalar(select(BusinessProfile).where(BusinessProfile.organization_id == org_id))
    out: list[AgentInsight] = []
    if profile and profile.employee_count:
        out.append(
            _insight(
                "HR", f"Headcount: {profile.employee_count}",
                f"The organization operates with ~{profile.employee_count} people.",
                "info", 65.0, ["business_profiles"], metric=str(profile.employee_count),
            )
        )
    # Capacity signal: a cluster of overdue tasks often means under-resourcing.
    today = date.today()
    overdue = len(
        list(
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
    )
    if overdue >= 3:
        out.append(
            _insight(
                "HR", "Possible capacity gap",
                f"{overdue} overdue tasks across projects may indicate under-resourcing.",
                "warning", 64.0, ["tasks"], action="Review staffing on the most overdue project.",
            )
        )
    if not out:
        out.append(
            _insight(
                "HR", "No people signals yet",
                "Add headcount in business discovery to activate capacity intelligence.",
                "info", 55.0, ["business_profiles"],
            )
        )
    return out


def _stratiqa_one(db: DBSession, org_id: uuid.UUID) -> list[AgentInsight]:
    """Master synthesis across the specialist agents."""
    risks = _risk(db, org_id)
    open_risks = [i for i in risks if i.severity in {"danger", "warning"}]
    pending_recs = len(
        list(
            db.scalars(
                select(Recommendation).where(
                    Recommendation.organization_id == org_id,
                    Recommendation.status == "pending",
                )
            ).all()
        )
    )
    goals = list(
        db.scalars(
            select(StrategicGoal).where(
                StrategicGoal.organization_id == org_id, StrategicGoal.status == "active"
            )
        ).all()
    )
    behind = 0
    for g in goals:
        latest = db.scalar(
            select(GoalProgress)
            .where(GoalProgress.goal_id == g.id)
            .order_by(GoalProgress.recorded_at.desc())
        )
        prog = float(latest.progress_percentage) if latest else 0.0
        if g.target_date and prog < 50 and (g.target_date - date.today()).days <= 60:
            behind += 1

    out = [
        _insight(
            "STRATIQA_ONE", "Executive synthesis",
            f"Tracking {len(goals)} active goal(s), {len(open_risks)} elevated risk(s), "
            f"and {pending_recs} recommendation(s) awaiting review.",
            "danger" if open_risks else "info", 80.0,
            ["strategic_goals", "project_risks", "recommendations"],
        )
    ]
    if behind:
        out.append(
            _insight(
                "STRATIQA_ONE", f"{behind} goal(s) at risk of slipping",
                f"{behind} goal(s) are under 50% with ≤60 days to target.",
                "warning", 74.0, ["strategic_goals + goal_progress"],
                action="Re-scope or add resources before the target date.",
            )
        )
    return out


_GENERATORS = {
    "STRATIQA_ONE": _stratiqa_one,
    "FINANCE": _finance,
    "SALES": _sales,
    "PROJECT": _project,
    "RISK": _risk,
    "CUSTOMER_SUCCESS": _customer,
    "PRODUCT": _product,
    "HR": _hr,
}


def insights_for(db: DBSession, org_id: uuid.UUID, agent_type: str) -> list[AgentInsight]:
    gen = _GENERATORS.get(agent_type)
    return gen(db, org_id) if gen else []


def _top_severity(insights: list[AgentInsight]) -> str:
    if not insights:
        return "info"
    return max(insights, key=lambda i: _SEVERITY_RANK.get(i.severity, 0)).severity


def roster(db: DBSession, org_id: uuid.UUID) -> AgentRoster:
    ensure_agents(db, org_id)
    summaries: list[AgentSummary] = []
    for agent_type, (name, domain) in AGENT_DEFS.items():
        insights = insights_for(db, org_id, agent_type)
        headline = insights[0].title if insights else "All clear"
        summaries.append(
            AgentSummary(
                agent_type=agent_type,
                name=name,
                domain=domain,
                status="active",
                headline=headline,
                insight_count=len(insights),
                top_severity=_top_severity(insights),
            )
        )
    return AgentRoster(agents=summaries, generated_at=datetime.utcnow())


def detail(db: DBSession, org_id: uuid.UUID, agent_type: str) -> AgentDetail | None:
    if agent_type not in AGENT_DEFS:
        return None
    ensure_agents(db, org_id)
    name, domain = AGENT_DEFS[agent_type]
    return AgentDetail(
        agent_type=agent_type,
        name=name,
        domain=domain,
        status="active",
        insights=insights_for(db, org_id, agent_type),
    )


def ask(db: DBSession, org_id: uuid.UUID, agent_type: str, query: str) -> AgentAskResponse | None:
    if agent_type not in AGENT_DEFS:
        return None
    agents = ensure_agents(db, org_id)
    name, _domain = AGENT_DEFS[agent_type]
    insights = insights_for(db, org_id, agent_type)

    if insights:
        answer = f"{insights[0].title}. " + " ".join(i.finding for i in insights[:3])
        confidence = round(sum(i.confidence_score for i in insights[:3]) / len(insights[:3]), 1)
        sources = sorted({s for i in insights for s in i.data_sources})
    else:
        answer = f"The {name} has no signals in your data yet."
        confidence = 50.0
        sources = []

    # Log the interaction against the agent (exercises the agent_interactions table).
    agent = next((a for a in agents if a.agent_type == agent_type), None)
    if agent is not None:
        db.add(AgentInteraction(agent_id=agent.id, query=query, response=answer))
        db.flush()

    return AgentAskResponse(
        agent_type=agent_type,
        name=name,
        answer=answer,
        confidence_score=confidence,
        data_sources=sources,
        insights=insights,
    )
