"""Business Discovery Engine.

Turns a founder interview into a Business Profile, Business DNA, and a
Business Blueprint. MVP uses transparent rule-based heuristics (no black box),
which keeps every derived attribute explainable — a core STRATIQA principle.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.models.discovery import BusinessBlueprint, BusinessDNA, BusinessProfile
from app.models.goals import GoalProgress, StrategicGoal
from app.schemas.discovery import FounderInterview
from app.services import recommendation_engine

# --- Heuristic tables --------------------------------------------------------

_REVENUE_STAGE = [
    (0, "ideation"),
    (100_000, "early_stage"),
    (1_000_000, "growth"),
    (10_000_000, "scale_up"),
    (100_000_000, "enterprise"),
]

_HIGH_RISK_INDUSTRIES = {"crypto", "fintech", "biotech", "gaming", "real estate"}
_LOW_COMPLEXITY_MODELS = {"saas", "subscription", "digital", "freelance", "agency"}
_HIGH_COMPLEXITY_MODELS = {"manufacturing", "logistics", "retail", "marketplace", "hardware"}


def _growth_stage(revenue: float | None, employees: int | None) -> str:
    rev = revenue or 0
    stage = "ideation"
    for threshold, label in _REVENUE_STAGE:
        if rev >= threshold:
            stage = label
    if (employees or 0) > 200 and stage in {"ideation", "early_stage"}:
        stage = "growth"
    return stage


def _risk_profile(interview: FounderInterview) -> str:
    industry = (interview.industry or "").lower()
    challenges = len(interview.main_challenges)
    if any(k in industry for k in _HIGH_RISK_INDUSTRIES) or challenges >= 4:
        return "elevated"
    if challenges >= 2:
        return "moderate"
    return "contained"


def _operational_complexity(interview: FounderInterview) -> str:
    model = (interview.business_model or "").lower()
    employees = interview.employee_count or 0
    if any(k in model for k in _HIGH_COMPLEXITY_MODELS) or employees > 250:
        return "high"
    if any(k in model for k in _LOW_COMPLEXITY_MODELS) and employees <= 50:
        return "low"
    return "moderate"


def _market_type(interview: FounderInterview) -> str:
    target = (interview.target_market or "").lower()
    if "enterprise" in target or "b2b" in target:
        return "B2B"
    if "consumer" in target or "b2c" in target:
        return "B2C"
    return "mixed"


def run_discovery(
    db: DBSession, organization_id: uuid.UUID, interview: FounderInterview
) -> tuple[BusinessProfile, BusinessDNA, BusinessBlueprint]:
    """Execute the full discovery pipeline and persist the results."""

    profile = BusinessProfile(
        organization_id=organization_id,
        industry=interview.industry,
        business_model=interview.business_model,
        company_size=interview.company_size,
        annual_revenue=interview.annual_revenue,
        employee_count=interview.employee_count,
    )
    db.add(profile)

    growth = _growth_stage(interview.annual_revenue, interview.employee_count)
    risk = _risk_profile(interview)
    complexity = _operational_complexity(interview)
    market = _market_type(interview)

    dna = BusinessDNA(
        organization_id=organization_id,
        growth_stage=growth,
        risk_profile=risk,
        operational_complexity=complexity,
        market_type=market,
    )
    db.add(dna)

    blueprint_json = {
        "industry": interview.industry,
        "revenue_model": interview.business_model,
        "growth_profile": growth,
        "risk_profile": risk,
        "operational_complexity": complexity,
        "market_type": market,
        "stated_goals": interview.primary_goals,
        "key_challenges": interview.main_challenges,
        "recommended_focus_areas": _focus_areas(growth, risk, complexity),
        "suggested_kpis": _suggested_kpis(market, interview.business_model),
    }
    blueprint = BusinessBlueprint(
        organization_id=organization_id, blueprint_json=blueprint_json
    )
    db.add(blueprint)
    db.flush()

    # Make the org non-empty from day one: turn the founder's *own* stated goals
    # into tracked strategic goals (grounded, not generic), then surface any
    # data-derived recommendations.
    _seed_goals_from_interview(db, organization_id, interview)
    recommendation_engine.refresh_recommendations(db, organization_id)

    return profile, dna, blueprint


# --- Goal classification + seeding ------------------------------------------

_GOAL_TYPE_KEYWORDS: dict[str, list[str]] = {
    "revenue": ["revenue", "arr", "mrr", "sales", "income", "bookings"],
    "expansion": ["expand", "market", "launch", "international", "geograph", "region"],
    "team": ["hire", "team", "headcount", "talent", "culture", "recruit"],
    "financial": ["cost", "margin", "efficien", "profit", "burn", "runway", "fundrais"],
    "product": ["product", "feature", "roadmap", "platform", "ship"],
    "customer": ["customer", "retention", "churn", "nps", "support", "success"],
}


def _classify_goal(text: str) -> str:
    """Transparent keyword classifier — keeps the goal_type explainable."""
    lowered = text.lower()
    for goal_type, keywords in _GOAL_TYPE_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return goal_type
    return "strategic"


def _seed_goals_from_interview(
    db: DBSession, organization_id: uuid.UUID, interview: FounderInterview
) -> int:
    """Create StrategicGoals from the founder's stated goals. Idempotent: skips
    any goal whose title already exists for the org (safe to re-run discovery)."""
    existing = {
        (title or "").strip().lower()
        for title in db.scalars(
            select(StrategicGoal.title).where(
                StrategicGoal.organization_id == organization_id
            )
        ).all()
    }
    target = date.today() + timedelta(days=90)
    created = 0
    for raw in interview.primary_goals:
        title = raw.strip()
        if not title or title.lower() in existing:
            continue
        goal = StrategicGoal(
            organization_id=organization_id,
            title=title[:255],
            description="Captured during business discovery.",
            goal_type=_classify_goal(title),
            target_date=target,
            status="active",
        )
        db.add(goal)
        db.flush()
        db.add(GoalProgress(goal_id=goal.id, progress_percentage=0))
        existing.add(title.lower())
        created += 1
    return created


def _focus_areas(growth: str, risk: str, complexity: str) -> list[str]:
    areas: list[str] = []
    if growth in {"ideation", "early_stage"}:
        areas += ["Product-market fit", "Customer acquisition", "Runway management"]
    elif growth in {"growth", "scale_up"}:
        areas += ["Operational scaling", "Unit economics", "Team expansion"]
    else:
        areas += ["Market defense", "Margin optimization", "Strategic M&A"]
    if risk == "elevated":
        areas.append("Risk mitigation framework")
    if complexity == "high":
        areas.append("Process standardization")
    return areas


def _suggested_kpis(market: str, model: str | None) -> list[str]:
    base = ["Monthly Recurring Revenue", "Gross Margin", "Cash Runway", "Net Profit"]
    if market == "B2B":
        base += ["Pipeline Value", "Sales Cycle Length", "Logo Retention"]
    else:
        base += ["Customer Acquisition Cost", "Lifetime Value", "Churn Rate"]
    if model and "subscription" in model.lower():
        base.append("Net Revenue Retention")
    return base
