"""Knowledge Graph schemas — nodes + edges for the org's entity graph."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    category: str
    value: float | None = None
    detail: str | None = None


class GraphEdge(BaseModel):
    source: str
    target: str
    type: str


class GraphOut(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    stats: dict[str, int]
    generated_at: datetime
