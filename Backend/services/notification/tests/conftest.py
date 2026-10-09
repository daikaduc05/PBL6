"""Test fixtures.

A dummy DATABASE_URL is injected before the app is imported: settings are read
lazily (``get_settings`` is cached), but the readiness probe still needs a
parseable URL. No test here opens a real connection.
"""

import os

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/postgres")
os.environ.setdefault("DEBUG", "false")

from httpx import ASGITransport, AsyncClient  # noqa: E402

from notification.main import create_app  # noqa: E402


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
