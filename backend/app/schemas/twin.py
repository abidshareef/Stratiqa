"""Digital Business Twin (simulation) schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class SimulationInput(BaseModel):
    """A 'what happens if...' scenario.

    Levers are percentage deltas (e.g. marketing_spend_change=25 -> +25%).
    """

    scenario_name: str = Field(min_length=2, max_length=255)
    scenario_description: str | None = None
    marketing_spend_change: float = 0.0
    hiring_change: float = 0.0
    price_change: float = 0.0
    market_expansion: float = 0.0
    new_product_launch: bool = False


class SimulationOutcome(BaseModel):
    revenue_impact: float
    profit_impact: float
    risk_impact: float
    growth_impact: float
    narrative: str
    confidence_score: float


class SimulationOut(ORMModel):
    id: uuid.UUID
    scenario_name: str
    scenario_description: str | None
    inputs: dict
    created_at: datetime


class SimulationResultOut(BaseModel):
    simulation: SimulationOut
    outcome: SimulationOutcome
