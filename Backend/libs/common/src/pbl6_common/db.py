"""Async SQLAlchemy engine/session plumbing shared by every service.

Each service creates its own engine (own DATABASE_URL, own `search_path`
pointing at its own Supabase schema — no cross-service reads) but reuses
this factory code and declarative Base.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base. Each service still owns only its own tables."""


def make_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(database_url, pool_pre_ping=True)


def make_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


def make_get_db(session_factory: async_sessionmaker[AsyncSession]):
    """Returns a FastAPI dependency bound to this service's session factory."""

    async def get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    return get_db
