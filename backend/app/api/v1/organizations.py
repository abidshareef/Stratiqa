"""Organization endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select

from app.core.deps import CurrentOrgId, CurrentUser, DbDep
from app.models.identity import Organization, OrganizationUser
from app.schemas.auth import OrganizationOut

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("", response_model=list[OrganizationOut])
def list_my_organizations(db: DbDep, user: CurrentUser):
    orgs = db.scalars(
        select(Organization)
        .join(OrganizationUser, OrganizationUser.organization_id == Organization.id)
        .where(OrganizationUser.user_id == user.id)
    ).all()
    return orgs


@router.get("/current", response_model=OrganizationOut)
def current_organization(db: DbDep, org_id: CurrentOrgId):
    return db.get(Organization, org_id)
