"""Digital Business Twin — rule-based simulation engine (MVP).

Takes a 'what happens if...' scenario (percentage levers) and projects impact
across revenue, profit, risk, and growth. The model is intentionally transparent
and explainable; coefficients are documented so outputs can be defended.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.models.analytics import KPI
from app.models.discovery import BusinessDNA
from app.models.twin import Simulation, SimulationResult
from app.schemas.twin import SimulationInput, SimulationOutcome

# Sensitivity coefficients: fraction of revenue lift per 1% lever change.
# Documented for explainability — these are first-order elasticity estimates.
_MARKETING_REVENUE_ELASTICITY = 0.35   # +1% marketing -> +0.35% revenue
_PRICE_REVENUE_ELASTICITY = -0.40      # +1% price -> -0.40% volume (net effect modeled below)
_EXPANSION_REVENUE_ELASTICITY = 0.50
_HIRING_COST_FACTOR = 0.6              # hiring adds cost faster than immediate revenue
_NEW_PRODUCT_REVENUE_LIFT = 8.0        # flat % lift assumption for a launch
_NEW_PRODUCT_RISK_LIFT = 12.0

_RISK_BASELINE = {"contained": 10.0, "moderate": 20.0, "elevated": 35.0}


def _baseline_risk(db: DBSession, org_id: uuid.UUID) -> float:
    dna = db.scalar(select(BusinessDNA).where(BusinessDNA.organization_id == org_id))
    if dna and dna.risk_profile in _RISK_BASELINE:
        return _RISK_BASELINE[dna.risk_profile]
    return 20.0


def simulate(db: DBSession, org_id: uuid.UUID, payload: SimulationInput) -> SimulationOutcome:
    """Compute projected impact for a scenario. Pure function over inputs + DNA."""

    # Revenue impact (%) — sum of lever contributions.
    price_volume_effect = _PRICE_REVENUE_ELASTICITY * payload.price_change
    price_revenue_effect = payload.price_change + price_volume_effect  # net of volume loss
    revenue_impact = (
        _MARKETING_REVENUE_ELASTICITY * payload.marketing_spend_change
        + _EXPANSION_REVENUE_ELASTICITY * payload.market_expansion
        + price_revenue_effect
        + (_NEW_PRODUCT_REVENUE_LIFT if payload.new_product_launch else 0.0)
    )

    # Cost impact drives profit alongside revenue.
    cost_impact = (
        0.5 * payload.marketing_spend_change
        + _HIRING_COST_FACTOR * payload.hiring_change
        + 0.3 * payload.market_expansion
        + (3.0 if payload.new_product_launch else 0.0)
    )
    profit_impact = revenue_impact - cost_impact

    # Risk impact (%) relative to DNA baseline.
    baseline_risk = _baseline_risk(db, org_id)
    risk_impact = (
        0.15 * abs(payload.market_expansion)
        + 0.10 * abs(payload.hiring_change)
        + 0.08 * abs(payload.price_change)
        + (_NEW_PRODUCT_RISK_LIFT if payload.new_product_launch else 0.0)
    )
    risk_impact = min(risk_impact, 100.0 - baseline_risk)

    # Growth impact blends revenue momentum and expansion.
    growth_impact = 0.6 * revenue_impact + 0.4 * payload.market_expansion

    narrative = _narrative(payload, revenue_impact, profit_impact, risk_impact, growth_impact)

    # Confidence: higher when fewer simultaneous levers are pulled (less interaction risk).
    active_levers = sum(
        1
        for v in (
            payload.marketing_spend_change,
            payload.hiring_change,
            payload.price_change,
            payload.market_expansion,
        )
        if v
    ) + (1 if payload.new_product_launch else 0)
    confidence = max(45.0, 85.0 - 7.0 * max(0, active_levers - 1))

    return SimulationOutcome(
        revenue_impact=round(revenue_impact, 1),
        profit_impact=round(profit_impact, 1),
        risk_impact=round(risk_impact, 1),
        growth_impact=round(growth_impact, 1),
        narrative=narrative,
        confidence_score=round(confidence, 1),
    )


def _narrative(
    p: SimulationInput, rev: float, profit: float, risk: float, growth: float
) -> str:
    parts: list[str] = []
    if p.marketing_spend_change:
        parts.append(f"a {p.marketing_spend_change:+.0f}% marketing change")
    if p.hiring_change:
        parts.append(f"a {p.hiring_change:+.0f}% hiring change")
    if p.price_change:
        parts.append(f"a {p.price_change:+.0f}% price change")
    if p.market_expansion:
        parts.append(f"{p.market_expansion:+.0f}% market expansion")
    if p.new_product_launch:
        parts.append("a new product launch")
    levers = ", ".join(parts) if parts else "no changes"
    direction = "improve" if profit >= 0 else "compress"
    return (
        f"With {levers}, the model projects revenue to move {rev:+.1f}% and profit to "
        f"{direction} by {abs(profit):.1f}%. Operating risk rises ~{risk:.1f} points and "
        f"the growth trajectory shifts {growth:+.1f}%. Validate against live KPIs before acting."
    )


def persist_simulation(
    db: DBSession,
    org_id: uuid.UUID,
    payload: SimulationInput,
    outcome: SimulationOutcome,
) -> Simulation:
    sim = Simulation(
        organization_id=org_id,
        scenario_name=payload.scenario_name,
        scenario_description=payload.scenario_description,
        inputs=payload.model_dump(),
    )
    db.add(sim)
    db.flush()
    db.add(
        SimulationResult(
            simulation_id=sim.id,
            predicted_outcome=outcome.model_dump(),
            confidence_score=outcome.confidence_score,
        )
    )
    db.flush()
    return sim


# Referenced for completeness; KPI anchoring can scale % impacts to absolute values.
def latest_revenue_kpi(db: DBSession, org_id: uuid.UUID) -> float | None:
    kpi = db.scalar(
        select(KPI)
        .where(KPI.organization_id == org_id, KPI.kpi_name.ilike("%revenue%"))
        .order_by(KPI.recorded_at.desc())
    )
    return float(kpi.value) if kpi and kpi.value is not None else None
