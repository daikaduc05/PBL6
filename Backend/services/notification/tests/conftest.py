"""Test fixtures.

Two kinds of test live here:

* ``client`` — no database. Health liveness and wiring.
* ``api_client`` — real PostgreSQL in Docker, schema built by running the
  service's own ``alembic upgrade head``. The service relies on PostgreSQL
  schemas, ``gen_random_uuid()`` and ``ON CONFLICT``, none of which SQLite can
  emulate — and driving the real migrations means a model drifting from them
  fails the build instead of passing quietly.
"""

import os
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/postgres")
os.environ.setdefault("JWT_SECRET", "test-secret-not-used-by-this-service")

from httpx import ASGITransport, AsyncClient  # noqa: E402
from notification.deps import get_db  # noqa: E402
from notification.main import create_app  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine  # noqa: E402
from sqlalchemy.pool import NullPool  # noqa: E402

SERVICE_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
async def client(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


# --------------------------------------------------------------------------
# Database-backed fixtures
# --------------------------------------------------------------------------


def _ensure_docker_host() -> None:
    """Point the Docker SDK at the active context's endpoint.

    Docker Desktop on Windows listens on ``npipe:////./pipe/dockerDesktopLinuxEngine``
    while the Python SDK defaults to ``npipe:////./pipe/docker_engine``, so the
    container fails to start with "cannot find the file specified" even though
    the ``docker`` CLI works. Asking the CLI for the real endpoint keeps this
    working without a hand-set DOCKER_HOST.
    """
    if os.environ.get("DOCKER_HOST"):
        return
    try:
        endpoint = subprocess.run(
            ["docker", "context", "inspect", "--format", "{{.Endpoints.docker.Host}}"],
            capture_output=True,
            text=True,
            timeout=15,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return
    if endpoint:
        os.environ["DOCKER_HOST"] = endpoint


def _run_migrations(url: str) -> None:
    """Run `alembic upgrade head` against the throwaway database.

    A subprocess rather than Alembic's Python API: ``get_settings`` is an
    lru_cache that already holds the dummy URL by the time fixtures run, and a
    separate process picks up DATABASE_URL cleanly — the same command the team
    runs by hand.
    """
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=SERVICE_DIR,
        env={**os.environ, "DATABASE_URL": url},
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"alembic upgrade failed:\n{result.stdout}\n{result.stderr}")


@pytest.fixture(scope="session")
def pg_url() -> Iterator[str]:
    try:
        from testcontainers.community.postgres import PostgresContainer
    except ImportError:  # pragma: no cover - older testcontainers layout
        try:
            from testcontainers.postgres import PostgresContainer
        except ImportError:
            pytest.skip("testcontainers not installed")

    _ensure_docker_host()

    try:
        container = PostgresContainer("postgres:16-alpine")
        container.start()
    except Exception as exc:  # pragma: no cover - Docker unavailable
        pytest.skip(f"Docker not available ({type(exc).__name__}: {exc})")

    url = (
        f"postgresql+asyncpg://{container.username}:{container.password}"
        f"@{container.get_container_host_ip()}:{container.get_exposed_port(5432)}"
        f"/{container.dbname}"
    )
    try:
        _run_migrations(url)
        yield url
    finally:
        container.stop()


@pytest.fixture
async def session(pg_url):
    """A session whose writes are rolled back after the test.

    ``join_transaction_mode="create_savepoint"`` lets the request pipeline
    commit for real — the commit lands on a savepoint, and rolling back the
    outer transaction leaves the database clean for the next test.
    """
    engine = create_async_engine(pg_url, poolclass=NullPool)
    async with engine.connect() as conn:
        outer = await conn.begin()
        db = AsyncSession(
            bind=conn, expire_on_commit=False, join_transaction_mode="create_savepoint"
        )
        try:
            yield db
        finally:
            await db.close()
            await outer.rollback()
    await engine.dispose()


@pytest.fixture
async def api_client(app, session):
    """Client whose requests run against the rolled-back test session."""

    async def _override():
        # Mirrors pbl6_common.db.make_get_db, which commits once per request.
        yield session
        await session.commit()

    app.dependency_overrides[get_db] = _override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
