"""Product Intelligence endpoints — catalog, inventory, demand, grounded signals."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.deps import CurrentOrgId, DbDep
from app.schemas.products import ProductOverview
from app.services import product_intelligence

router = APIRouter(prefix="/products", tags=["product-intelligence"])


@router.get("", response_model=ProductOverview)
def product_overview(db: DbDep, org_id: CurrentOrgId):
    return product_intelligence.overview(db, org_id)
