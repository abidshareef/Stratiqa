"""Section 1: Identity & Access Management."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDPk
from app.models._types import fk, fk_optional


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[UUIDPk]
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255))
    avatar_url: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_secret: Mapped[str | None] = mapped_column(Text)  # TOTP secret (store encrypted in prod)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id: Mapped[UUIDPk]
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(120))
    business_stage: Mapped[str | None] = mapped_column(String(60))
    country: Mapped[str | None] = mapped_column(String(120))
    timezone: Mapped[str | None] = mapped_column(String(60))
    created_by = fk_optional("users.id")


class Role(Base, TimestampMixin):
    __tablename__ = "roles"

    id: Mapped[UUIDPk]
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)


class Permission(Base, TimestampMixin):
    __tablename__ = "permissions"

    id: Mapped[UUIDPk]
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)


class RolePermission(Base):
    __tablename__ = "role_permissions"
    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="role_permission"),)

    id: Mapped[UUIDPk]
    role_id = fk("roles.id")
    permission_id = fk("permissions.id")


class OrganizationUser(Base):
    __tablename__ = "organization_users"
    __table_args__ = (UniqueConstraint("organization_id", "user_id", name="org_user"),)

    id: Mapped[UUIDPk]
    organization_id = fk("organizations.id")
    user_id = fk("users.id")
    role_id = fk_optional("roles.id")
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[UUIDPk]
    user_id = fk("users.id")
    jwt_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    device_info: Mapped[str | None] = mapped_column(Text)
    ip_address: Mapped[str | None] = mapped_column(String(64))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
