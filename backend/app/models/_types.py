"""Shared column helpers for models (UUID FKs, etc.).

These helpers return ``mapped_column(...)`` objects. Assign them WITHOUT a
left-hand ``Mapped[...]`` annotation, e.g. ``organization_id = fk("organizations.id")``.
SQLAlchemy 2.0 fully supports non-annotated ``mapped_column`` assignments; the
Python/foreign-key type is carried by the column definition itself.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PgUUID  # noqa: N811
from sqlalchemy.orm import mapped_column


def fk(target: str, *, ondelete: str = "CASCADE") -> Any:
    """A required UUID foreign-key column. ``target`` is e.g. 'organizations.id'."""
    return mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey(target, ondelete=ondelete),
        nullable=False,
        index=True,
    )


def fk_optional(target: str, ondelete: str = "SET NULL") -> Any:
    """A nullable UUID foreign-key column."""
    return mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey(target, ondelete=ondelete),
        nullable=True,
        index=True,
    )
