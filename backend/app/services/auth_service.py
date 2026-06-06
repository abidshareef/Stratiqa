"""Authentication service — registration, login, token refresh, MFA, sessions."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pyotp
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.identity import (
    Organization,
    OrganizationUser,
    Role,
    Session,
    User,
)
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services import audit

# Default roles seeded per organization on creation.
DEFAULT_ROLES = ["Owner", "CEO", "Manager", "Analyst", "Employee"]


def _ensure_default_roles(db: DBSession) -> dict[str, Role]:
    roles: dict[str, Role] = {}
    for name in DEFAULT_ROLES:
        role = db.scalar(select(Role).where(Role.name == name))
        if role is None:
            role = Role(name=name, description=f"{name} role")
            db.add(role)
            db.flush()
        roles[name] = role
    return roles


def _persist_session(
    db: DBSession, user: User, jti: str, device: str | None, ip: str | None
) -> None:
    db.add(
        Session(
            user_id=user.id,
            jwt_id=jti,
            device_info=device,
            ip_address=ip,
            expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_days),
        )
    )


def register(
    db: DBSession, payload: RegisterRequest, *, ip: str | None = None
) -> tuple[User, Organization]:
    existing = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )

    user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    db.flush()

    org = Organization(name=payload.organization_name, created_by=user.id)
    db.add(org)
    db.flush()

    roles = _ensure_default_roles(db)
    db.add(
        OrganizationUser(
            organization_id=org.id, user_id=user.id, role_id=roles["Owner"].id
        )
    )
    audit.record(
        db,
        action="user.register",
        user_id=user.id,
        organization_id=org.id,
        resource="user",
        ip_address=ip,
    )
    db.flush()
    return user, org


def _issue_tokens(
    db: DBSession, user: User, *, device: str | None, ip: str | None
) -> dict[str, str]:
    access, _ = create_access_token(str(user.id), email=user.email)
    refresh, jti = create_refresh_token(str(user.id))
    _persist_session(db, user, jti, device, ip)
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}


def login(
    db: DBSession,
    payload: LoginRequest,
    *,
    device: str | None = None,
    ip: str | None = None,
) -> tuple[User, Organization, dict[str, str]]:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        audit.record(db, action="user.login.failed", resource=payload.email, ip_address=ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    if user.mfa_enabled:
        if not payload.mfa_code:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="MFA code required"
            )
        if not user.mfa_secret or not pyotp.TOTP(user.mfa_secret).verify(payload.mfa_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid MFA code"
            )

    membership = db.scalar(
        select(OrganizationUser).where(OrganizationUser.user_id == user.id)
    )
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="No organization for user"
        )
    org = db.get(Organization, membership.organization_id)

    user.last_login = datetime.now(UTC)
    tokens = _issue_tokens(db, user, device=device, ip=ip)
    audit.record(
        db,
        action="user.login",
        user_id=user.id,
        organization_id=org.id if org else None,
        ip_address=ip,
    )
    return user, org, tokens


def refresh(db: DBSession, refresh_token: str) -> dict[str, str]:
    try:
        payload = decode_token(refresh_token)
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        ) from exc
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not a refresh token"
        )

    jti = payload.get("jti")
    sess = db.scalar(select(Session).where(Session.jwt_id == jti))
    if sess is None or sess.revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Session revoked"
        )

    user = db.get(User, uuid.UUID(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user")

    # Rotate: revoke old session, issue new pair.
    sess.revoked = True
    return _issue_tokens(db, user, device=sess.device_info, ip=sess.ip_address)


def logout(db: DBSession, user: User) -> None:
    sessions = db.scalars(
        select(Session).where(Session.user_id == user.id, Session.revoked.is_(False))
    ).all()
    for sess in sessions:
        sess.revoked = True
    audit.record(db, action="user.logout", user_id=user.id)


def setup_mfa(db: DBSession, user: User) -> tuple[str, str]:
    secret = pyotp.random_base32()
    user.mfa_secret = secret
    user.mfa_enabled = True
    otpauth = pyotp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="STRATIQA")
    audit.record(db, action="user.mfa.enable", user_id=user.id)
    return secret, otpauth
