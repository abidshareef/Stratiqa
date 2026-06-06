"""Recommendation endpoints — list, regenerate, accept/dismiss, feedback."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.deps import CurrentOrgId, DbDep
from app.models.recommendations import Recommendation, RecommendationFeedback
from app.schemas.recommendation import FeedbackIn, RecommendationOut
from app.services import recommendation_engine

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


def _get_owned(db, org_id: uuid.UUID, rec_id: uuid.UUID) -> Recommendation:
    rec = db.get(Recommendation, rec_id)
    if rec is None or rec.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found"
        )
    return rec


@router.get("", response_model=list[RecommendationOut])
def list_recommendations(db: DbDep, org_id: CurrentOrgId):
    return db.scalars(
        select(Recommendation)
        .where(Recommendation.organization_id == org_id)
        .order_by(Recommendation.confidence_score.desc())
    ).all()


@router.post("/refresh", response_model=list[RecommendationOut])
def refresh(db: DbDep, org_id: CurrentOrgId):
    return recommendation_engine.refresh_recommendations(db, org_id)


@router.post("/{rec_id}/accept", response_model=RecommendationOut)
def accept(rec_id: uuid.UUID, db: DbDep, org_id: CurrentOrgId):
    rec = _get_owned(db, org_id, rec_id)
    rec.status = "accepted"
    db.flush()
    return rec


@router.post("/{rec_id}/dismiss", response_model=RecommendationOut)
def dismiss(rec_id: uuid.UUID, db: DbDep, org_id: CurrentOrgId):
    rec = _get_owned(db, org_id, rec_id)
    rec.status = "dismissed"
    db.flush()
    return rec


@router.post("/{rec_id}/feedback", response_model=RecommendationOut)
def feedback(rec_id: uuid.UUID, payload: FeedbackIn, db: DbDep, org_id: CurrentOrgId):
    rec = _get_owned(db, org_id, rec_id)
    db.add(
        RecommendationFeedback(
            recommendation_id=rec.id, accepted=payload.accepted, feedback=payload.feedback
        )
    )
    rec.status = "accepted" if payload.accepted else "dismissed"
    db.flush()
    return rec
