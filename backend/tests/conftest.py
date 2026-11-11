"""Pytest fixtures.

The full stack is exercised against a throwaway SQLite database so the suite
runs with zero external infrastructure (no Postgres/Redis/Qdrant). The DB URL is
set *before* any ``app`` import so the cached settings and the module-level
engine bind to it. Production still targets PostgreSQL — the model layer is
dialect-portable (see ``app.core.database``).
"""

from __future__ import annotations

import os
import pathlib
import tempfile

# --- Must run before importing anything under ``app`` ---------------------
_DB_PATH = pathlib.Path(tempfile.gettempdir()) / "stratiqa_test.db"
if _DB_PATH.exists():
    _DB_PATH.unlink()
os.environ["STRATIQA_DATABASE_URL"] = f"sqlite+pysqlite:///{_DB_PATH.as_posix()}"
os.environ["STRATIQA_JWT_SECRET"] = "test-only-secret"
os.environ["STRATIQA_ENV"] = "test"
os.environ["STRATIQA_DEBUG"] = "false"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.scripts.seed import DEMO_EMAIL, DEMO_PASSWORD, seed  # noqa: E402

DEMO_EMAIL = DEMO_EMAIL
DEMO_PASSWORD = DEMO_PASSWORD


@pytest.fixture(scope="session", autouse=True)
def _seeded_db() -> None:
    """Create tables and seed the demo organization once for the session."""
    seed()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _login(client: TestClient, email: str, password: str) -> str:
    resp = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["tokens"]["access_token"]


@pytest.fixture
def auth_client(client: TestClient) -> TestClient:
    """A TestClient pre-authenticated as the seeded demo founder."""
    token = _login(client, DEMO_EMAIL, DEMO_PASSWORD)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client
