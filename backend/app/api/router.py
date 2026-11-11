"""Aggregate API router (v1)."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    agents,
    alerts,
    analytics,
    auth,
    briefs,
    customers,
    discovery,
    goals,
    governance,
    knowledge_graph,
    organizations,
    products,
    projects,
    recommendations,
    reports,
    stratiqa_one,
    twin,
    uploads,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(analytics.router)
api_router.include_router(organizations.router)
api_router.include_router(discovery.router)
api_router.include_router(goals.router)
api_router.include_router(projects.router)
api_router.include_router(recommendations.router)
api_router.include_router(reports.router)
api_router.include_router(briefs.router)
api_router.include_router(stratiqa_one.router)
api_router.include_router(twin.router)
api_router.include_router(knowledge_graph.router)
api_router.include_router(agents.router)
api_router.include_router(customers.router)
api_router.include_router(products.router)
api_router.include_router(alerts.router)
api_router.include_router(uploads.router)
api_router.include_router(governance.router)
