"""Audit logging helper — records security-relevant actions."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session as DBSession

from app.models.governance import AuditLog


def record(
    db: DBSession,
    *,
    action: str,
    user_id: uuid.UUID | None = None,
    organization_id: uuid.UUID | None = None,
    resource: str | None = None,
    detail: str | None = None,
    ip_address: str | None = None,
) -> None:
    db.add(
        AuditLog(
            user_id=user_id,
            organization_id=organization_id,
            action=action,
            resource=resource,
            detail=detail,
            ip_address=ip_address,
        )
    )
    db.flush()
