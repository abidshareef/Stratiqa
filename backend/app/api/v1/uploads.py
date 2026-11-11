"""Data ingestion endpoints: upload a business file, preview it, then commit
its rows into KPIs / customers / products."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from sqlalchemy import select

from app.core.deps import CurrentOrgId, CurrentUser, DbDep
from app.models.uploads import DataUpload
from app.schemas.common import Message
from app.schemas.upload import CommitMapping, CommitResult, UploadDetail, UploadOut
from app.services import ingestion

router = APIRouter(prefix="/uploads", tags=["data-ingestion"])

_MAX_BYTES = 15 * 1024 * 1024  # 15 MB


@router.post("", response_model=UploadDetail, status_code=status.HTTP_201_CREATED)
def upload_file(
    db: DbDep,
    org_id: CurrentOrgId,
    user: CurrentUser,
    file: UploadFile = File(...),
):
    raw = file.file.read()
    if not raw:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Empty file.")
    if len(raw) > _MAX_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File exceeds 15 MB.")
    return ingestion.ingest(
        db, org_id, user.id, file.filename or "upload", file.content_type, raw
    )


@router.get("", response_model=list[UploadOut])
def list_uploads(db: DbDep, org_id: CurrentOrgId):
    return db.scalars(
        select(DataUpload)
        .where(DataUpload.organization_id == org_id)
        .order_by(DataUpload.created_at.desc())
    ).all()


@router.get("/{upload_id}", response_model=UploadDetail)
def get_upload(upload_id: uuid.UUID, db: DbDep, org_id: CurrentOrgId):
    upload = ingestion.get_upload(db, org_id, upload_id)
    if upload is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Upload not found.")
    return upload


@router.post("/{upload_id}/commit", response_model=CommitResult)
def commit_upload(
    upload_id: uuid.UUID, mapping: CommitMapping, db: DbDep, org_id: CurrentOrgId
):
    upload = ingestion.get_upload(db, org_id, upload_id)
    if upload is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Upload not found.")
    if not upload.columns:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "This file has no tabular columns to map.",
        )
    try:
        return ingestion.commit(db, org_id, upload, mapping)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc


@router.delete("/{upload_id}", response_model=Message)
def delete_upload(upload_id: uuid.UUID, db: DbDep, org_id: CurrentOrgId):
    upload = ingestion.get_upload(db, org_id, upload_id)
    if upload is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Upload not found.")
    db.delete(upload)
    db.flush()
    return Message(message="Upload deleted.")
