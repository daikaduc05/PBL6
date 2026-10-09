"""Test fixtures.

Two kinds of test live here:

* ``client`` — no database. Health probes and header parsing.
* ``api_client`` — a real PostgreSQL in Docker, with the project's own DDL
  applied from ``Backend/db/*.sql``. The service uses PostgreSQL schemas,
  ``gen_random_uuid()`` and ``ON CONFLICT``, none of which SQLite can emulate.
  Running the real DDL also means a model drifting from the committed SQL
  shows up as a failing test.
"""

import asyncio
import os
import subprocess
from pathlib import Path

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/postgres")
os.environ.setdefault("DEBUG", "false")

from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine  # noqa: E402
from sqlalchemy.pool import NullPool  # noqa: E402

from notification.db import get_session  # noqa: E402
from notification.main import create_app  # noqa: E402

# tests/ -> notification/ -> services/ -> Backend/
DB_DIR = Path(__file__).resolve().parents[3] / "db"
DDL_FILES = (
    "00_schemas.sql",
    "05_notification.sql",
    "06_notification_processed_events.sql",
)


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


async def _apply_ddl(url: str) -> None:
    """Apply the committed SQL files with asyncpg directly.

    Not through SQLAlchemy: each file holds several statements, and asyncpg
    rejects multi-statement text when it goes through a prepared statement.
    Its own ``execute`` uses the simple query protocol, which accepts them.
    """
    import asyncpg

    conn = await asyncpg.connect(url.replace("postgresql+asyncpg://", "postgresql://"))
    try:
        for name in DDL_FILES:
            await conn.execute((DB_DIR / name).read_text(encoding="utf-8"))
    finally:
        await conn.close()


def _ensure_docker_host() -> None:
    """Point the Docker SDK at the active context's endpoint.

    Docker Desktop on Windows listens on ``npipe:////./pipe/dockerDesktopLinuxEngine``
    while the Python SDK defaults to ``npipe:////./pipe/docker_engine``, so
    container startup fails with "cannot find the file specified" even though
    the ``docker`` CLI works. Asking the CLI for the real endpoint keeps this
    working for everyone without a manual DOCKER_HOST.
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


@pytest.fixture(scope="session")
def pg_url() -> str:
    """Start PostgreSQL in Docker and apply the project DDL once per session."""
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
        asyncio.run(_apply_ddl(url))
        yield url
    finally:
        container.stop()


@pytest.fixture
async def session(pg_url):
    """A session whose writes are rolled back after the test.

    ``join_transaction_mode="create_savepoint"`` lets the endpoints call
    ``commit()`` for real — the commit lands on a savepoint, and rolling back
    the outer transaction leaves the database untouched for the next test.
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
        yield session

    app.dependency_overrides[get_session] = _override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
