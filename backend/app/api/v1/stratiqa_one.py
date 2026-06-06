"""STRATIQA One endpoints — executive home, war room, and ask."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.deps import CurrentOrgId, CurrentUser, DbDep
from app.schemas.stratiqa_one import AskRequest, AskResponse, ExecutiveHome, WarRoom
from app.services import stratiqa_one

router = APIRouter(prefix="/stratiqa-one", tags=["stratiqa-one"])


@router.get("/home", response_model=ExecutiveHome)
def home(db: DbDep, org_id: CurrentOrgId, user: CurrentUser):
    return stratiqa_one.executive_home(db, org_id, user.full_name)


@router.get("/war-room", response_model=WarRoom)
def war_room(db: DbDep, org_id: CurrentOrgId):
    return stratiqa_one.war_room(db, org_id)


@router.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest, db: DbDep, org_id: CurrentOrgId):
    return stratiqa_one.ask(db, org_id, payload.query)
