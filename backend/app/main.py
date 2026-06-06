"""STRATIQA FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RateLimitMiddleware, SecurityHeadersMiddleware
from app.schemas.common import HealthStatus

configure_logging()
logger = get_logger()

app = FastAPI(
    title=f"{settings.project_name} API",
    description="AI-Powered Business Operating System — backend.",
    version="0.1.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

# --- Middleware (order matters: security headers outermost) ---
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, max_requests=240, window_seconds=60)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routes ---
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/health", response_model=HealthStatus, tags=["system"])
def health() -> HealthStatus:
    return HealthStatus(status="ok", service=settings.project_name, version="0.1.0")


@app.get("/", tags=["system"])
def root() -> dict:
    return {
        "name": settings.project_name,
        "tagline": "AI-Powered Business Operating System",
        "docs": "/docs",
        "api_prefix": settings.api_prefix,
    }


@app.on_event("startup")
def _on_startup() -> None:
    logger.info("stratiqa.startup", env=settings.env, api_prefix=settings.api_prefix)
