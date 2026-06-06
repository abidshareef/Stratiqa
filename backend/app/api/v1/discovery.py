"""Business Discovery endpoints (founder interview → DNA → blueprint)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.deps import CurrentOrgId, DbDep
from app.models.discovery import BusinessBlueprint, BusinessDNA, BusinessProfile
from app.schemas.discovery import (
    BusinessBlueprintOut,
    BusinessDNAOut,
    BusinessProfileOut,
    DiscoveryResult,
    FounderInterview,
)
from app.services import discovery_service

router = APIRouter(prefix="/discovery", tags=["discovery"])


@router.post("/run", response_model=DiscoveryResult, status_code=status.HTTP_201_CREATED)
def run_discovery(payload: FounderInterview, db: DbDep, org_id: CurrentOrgId):
    profile, dna, blueprint = discovery_service.run_discovery(db, org_id, payload)
    return DiscoveryResult(
        profile=BusinessProfileOut.model_validate(profile),
        dna=BusinessDNAOut.model_validate(dna),
        blueprint=BusinessBlueprintOut.model_validate(blueprint),
    )


@router.get("/blueprint", response_model=BusinessBlueprintOut)
def latest_blueprint(db: DbDep, org_id: CurrentOrgId):
    bp = db.scalar(
        select(BusinessBlueprint)
        .where(BusinessBlueprint.organization_id == org_id)
        .order_by(BusinessBlueprint.generated_at.desc())
    )
    if bp is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No blueprint yet — run discovery first",
        )
    return bp


@router.get("/dna", response_model=BusinessDNAOut)
def latest_dna(db: DbDep, org_id: CurrentOrgId):
    dna = db.scalar(
        select(BusinessDNA)
        .where(BusinessDNA.organization_id == org_id)
        .order_by(BusinessDNA.generated_at.desc())
    )
    if dna is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No DNA yet")
    return dna


@router.get("/profile", response_model=BusinessProfileOut)
def latest_profile(db: DbDep, org_id: CurrentOrgId):
    profile = db.scalar(
        select(BusinessProfile).where(BusinessProfile.organization_id == org_id)
    )
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No profile yet")
    return profile
