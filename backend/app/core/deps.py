"""FastAPI dependencies: current user, current organization, DB session."""

from __future__ import annotations

import uuid
from typing import Annotated

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models.identity import OrganizationUser, User

bearer_scheme = HTTPBearer(auto_error=True)

DbDep = Annotated[DBSession, Depends(get_db)]


def get_current_user(
    db: DbDep,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> User:
    """Resolve and validate the access-token bearer into a User."""
    creds_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(credentials.credentials)
    except jwt.PyJWTError as exc:  # noqa: F841
        raise creds_exc from exc

    if payload.get("type") != "access":
        raise creds_exc

    user_id = payload.get("sub")
    if not user_id:
        raise creds_exc

    user = db.get(User, uuid.UUID(user_id))
    if user is None or not user.is_active:
        raise creds_exc
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_org_id(
    db: DbDep,
    user: CurrentUser,
    x_organization_id: Annotated[str | None, Header()] = None,
) -> uuid.UUID:
    """Resolve the active organization for this request.

    The client sends ``X-Organization-Id``. We verify the user is a member.
    If omitted and the user belongs to exactly one org, that org is used.
    """
    memberships = db.scalars(
        select(OrganizationUser).where(OrganizationUser.user_id == user.id)
    ).all()
    if not memberships:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not belong to any organization",
        )

    if x_organization_id:
        try:
            requested = uuid.UUID(x_organization_id)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid X-Organization-Id",
            ) from exc
        if not any(m.organization_id == requested for m in memberships):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of the requested organization",
            )
        return requested

    if len(memberships) == 1:
        return memberships[0].organization_id

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Multiple organizations — specify X-Organization-Id header",
    )


CurrentOrgId = Annotated[uuid.UUID, Depends(get_current_org_id)]
