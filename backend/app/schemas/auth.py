"""Authentication & identity schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import ORMModel


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)
    organization_name: str = Field(min_length=2, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    mfa_code: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOut(ORMModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str | None
    avatar_url: str | None
    is_active: bool
    mfa_enabled: bool
    last_login: datetime | None


class OrganizationOut(ORMModel):
    id: uuid.UUID
    name: str
    industry: str | None
    business_stage: str | None
    country: str | None
    timezone: str | None


class AuthResult(BaseModel):
    user: UserOut
    organization: OrganizationOut
    tokens: TokenPair


class MfaSetupOut(BaseModel):
    secret: str
    otpauth_url: str
