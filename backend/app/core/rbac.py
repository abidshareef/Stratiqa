"""Role-Based Access Control helpers.

Permissions are resolved from the user's role within the active organization.
``require_permission`` returns a dependency that enforces a named permission.
"""

from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.core.deps import CurrentOrgId, CurrentUser, DbDep
from app.models.identity import (
    OrganizationUser,
    Permission,
    Role,
    RolePermission,
)

# Roles that implicitly hold every permission.
SUPER_ROLES = {"Owner", "CEO"}


def get_user_permissions(db: DBSession, user_id: uuid.UUID, org_id: uuid.UUID) -> set[str]:
    membership = db.scalar(
        select(OrganizationUser).where(
            OrganizationUser.user_id == user_id,
            OrganizationUser.organization_id == org_id,
        )
    )
    if membership is None or membership.role_id is None:
        return set()

    role = db.get(Role, membership.role_id)
    if role is None:
        return set()
    if role.name in SUPER_ROLES:
        return {"*"}

    perms = db.scalars(
        select(Permission.name)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .where(RolePermission.role_id == role.id)
    ).all()
    return set(perms)


def require_permission(permission: str):
    """Dependency factory enforcing a named permission for the active org."""

    def _checker(db: DbDep, user: CurrentUser, org_id: CurrentOrgId) -> None:
        perms = get_user_permissions(db, user.id, org_id)
        if "*" in perms or permission in perms:
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing required permission: {permission}",
        )

    return Depends(_checker)
