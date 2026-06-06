"""Business Discovery schemas (founder interview → DNA → blueprint)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class FounderInterview(BaseModel):
    """Phase 1 inputs collected from the founder."""

    industry: str = Field(max_length=120)
    business_model: str = Field(max_length=120)
    company_size: str = Field(max_length=60)
    annual_revenue: float | None = None
    employee_count: int | None = None
    primary_goals: list[str] = Field(default_factory=list)
    main_challenges: list[str] = Field(default_factory=list)
    target_market: str | None = None


class BusinessProfileOut(ORMModel):
    id: uuid.UUID
    industry: str | None
    business_model: str | None
    company_size: str | None
    annual_revenue: float | None
    employee_count: int | None


class BusinessDNAOut(ORMModel):
    id: uuid.UUID
    growth_stage: str | None
    risk_profile: str | None
    operational_complexity: str | None
    market_type: str | None
    generated_at: datetime


class BusinessBlueprintOut(ORMModel):
    id: uuid.UUID
    blueprint_json: dict
    generated_at: datetime


class DiscoveryResult(BaseModel):
    profile: BusinessProfileOut
    dna: BusinessDNAOut
    blueprint: BusinessBlueprintOut
