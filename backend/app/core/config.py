"""Centralized application configuration.

All settings are loaded from environment variables (prefixed ``STRATIQA_``) or a
local ``.env`` file. Secrets are NEVER hardcoded — defaults here are safe for
local development only.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="STRATIQA_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- App ---
    env: str = "development"
    debug: bool = True
    project_name: str = "STRATIQA"
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # --- Security ---
    jwt_secret: str = "dev-insecure-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_days: int = 14
    bcrypt_rounds: int = 12

    # --- Data stores ---
    database_url: str = "postgresql+psycopg://stratiqa:stratiqa@localhost:5432/stratiqa"
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"

    # --- AI gateway (provider-agnostic) ---
    llm_provider: str = "none"
    llm_api_key: str = ""
    llm_model: str = ""

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def is_production(self) -> bool:
        return self.env.lower() in {"production", "prod"}


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


settings = get_settings()
