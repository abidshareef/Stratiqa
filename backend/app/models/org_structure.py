"""Section 2: Organization Structure."""

from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, UUIDPk
from app.models._types import fk, fk_optional


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[UUIDPk]
    organization_id = fk("organizations.id")
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[UUIDPk]
    department_id = fk("departments.id")
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    lead_user_id = fk_optional("users.id")


class TeamMember(Base):
    __tablename__ = "team_members"

    id: Mapped[UUIDPk]
    team_id = fk("teams.id")
    user_id = fk("users.id")
