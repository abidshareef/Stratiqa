"""Authentication endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Header, Request, status

from app.core.deps import CurrentUser, DbDep
from app.schemas.auth import (
    AuthResult,
    LoginRequest,
    MfaSetupOut,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
    UserOut,
)
from app.schemas.common import Message
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResult, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: DbDep, request: Request):
    ip = request.client.host if request.client else None
    user, org = auth_service.register(db, payload, ip=ip)
    tokens = auth_service.login(  # auto-login after register
        db, LoginRequest(email=payload.email, password=payload.password), ip=ip
    )[2]
    return AuthResult(user=user, organization=org, tokens=TokenPair(**tokens))


@router.post("/login", response_model=AuthResult)
def login(
    payload: LoginRequest,
    db: DbDep,
    request: Request,
    user_agent: str | None = Header(default=None),
):
    ip = request.client.host if request.client else None
    user, org, tokens = auth_service.login(db, payload, device=user_agent, ip=ip)
    return AuthResult(user=user, organization=org, tokens=TokenPair(**tokens))


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: DbDep):
    return TokenPair(**auth_service.refresh(db, payload.refresh_token))


@router.post("/logout", response_model=Message)
def logout(db: DbDep, user: CurrentUser):
    auth_service.logout(db, user)
    return Message(message="Logged out")


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser):
    return user


@router.post("/mfa/setup", response_model=MfaSetupOut)
def mfa_setup(db: DbDep, user: CurrentUser):
    secret, otpauth = auth_service.setup_mfa(db, user)
    return MfaSetupOut(secret=secret, otpauth_url=otpauth)
