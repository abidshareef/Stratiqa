"""Shared schema base classes and small response models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    """Base for schemas that read from ORM objects."""

    model_config = ConfigDict(from_attributes=True)


class Message(BaseModel):
    message: str


class HealthStatus(BaseModel):
    status: str
    service: str
    version: str
