"""Digital Business Twin endpoints — run and store simulations."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select

from app.core.deps import CurrentOrgId, DbDep
from app.models.twin import Simulation
from app.schemas.twin import (
    SimulationInput,
    SimulationOut,
    SimulationResultOut,
)
from app.services import business_twin

router = APIRouter(prefix="/twin", tags=["business-twin"])


@router.post("/simulate", response_model=SimulationResultOut)
def simulate(payload: SimulationInput, db: DbDep, org_id: CurrentOrgId):
    outcome = business_twin.simulate(db, org_id, payload)
    sim = business_twin.persist_simulation(db, org_id, payload, outcome)
    return SimulationResultOut(
        simulation=SimulationOut.model_validate(sim), outcome=outcome
    )


@router.get("/simulations", response_model=list[SimulationOut])
def list_simulations(db: DbDep, org_id: CurrentOrgId):
    return db.scalars(
        select(Simulation)
        .where(Simulation.organization_id == org_id)
        .order_by(Simulation.created_at.desc())
    ).all()
