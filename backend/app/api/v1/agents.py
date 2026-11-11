"""AI Agent endpoints — specialist agent roster, insights, and Q&A."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.core.deps import CurrentOrgId, DbDep
from app.schemas.agents import (
    AgentAskRequest,
    AgentAskResponse,
    AgentDetail,
    AgentRoster,
)
from app.services import agents

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=AgentRoster)
def list_agents(db: DbDep, org_id: CurrentOrgId):
    return agents.roster(db, org_id)


@router.get("/{agent_type}", response_model=AgentDetail)
def agent_detail(agent_type: str, db: DbDep, org_id: CurrentOrgId):
    result = agents.detail(db, org_id, agent_type.upper())
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown agent")
    return result


@router.post("/{agent_type}/ask", response_model=AgentAskResponse)
def agent_ask(agent_type: str, payload: AgentAskRequest, db: DbDep, org_id: CurrentOrgId):
    result = agents.ask(db, org_id, agent_type.upper(), payload.query)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown agent")
    return result
