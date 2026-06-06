"""Aggregate API router (v1)."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    analytics,
    auth,
    briefs,
    discovery,
    goals,
    organizations,
    projects,
    recommendations,
    reports,
    stratiqa_one,
    twin,
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
