"""Knowledge Graph endpoints — the org's entity/relationship graph."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.deps import CurrentOrgId, DbDep
from app.schemas.knowledge_graph import GraphOut
from app.services import knowledge_graph

router = APIRouter(prefix="/knowledge-graph", tags=["knowledge-graph"])


@router.get("", response_model=GraphOut)
def get_graph(db: DbDep, org_id: CurrentOrgId):
    # Build on first access so a freshly onboarded org sees its graph immediately.
    return knowledge_graph.get_graph(db, org_id, build_if_empty=True)


@router.post("/rebuild", response_model=GraphOut)
def rebuild_graph(db: DbDep, org_id: CurrentOrgId):
    return knowledge_graph.rebuild_graph(db, org_id)
