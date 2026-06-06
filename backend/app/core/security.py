"""Security primitives: password hashing and JWT token issuance/verification."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import jwt
from passlib.context import CryptContext

from app.core.config import settings

_pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.bcrypt_rounds,
)

TokenType = Literal["access", "refresh"]


# --- Passwords ---------------------------------------------------------------

def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


# --- JWT ---------------------------------------------------------------------

def _create_token(
    subject: str,
    token_type: TokenType,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """Return (encoded_jwt, jti)."""
    now = datetime.now(UTC)
    jti = str(uuid.uuid4())
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, jti


def create_access_token(subject: str, **claims: Any) -> tuple[str, str]:
    return _create_token(
        subject, "access", timedelta(minutes=settings.access_token_minutes), claims
    )


def create_refresh_token(subject: str, **claims: Any) -> tuple[str, str]:
    return _create_token(
        subject, "refresh", timedelta(days=settings.refresh_token_days), claims
    )


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT. Raises jwt exceptions on failure."""
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
