"""Async SQLAlchemy engine and session wiring for the shared Supabase database.

The service owns the ``notification`` schema. Tables of other bounded contexts
are reachable (one database) but are read-only and always fully qualified —
see ``recommendation/readers.py`` and spec §0.4.
"""

from collections.abc import AsyncGenerator
from functools import lru_cache
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from notification.config import get_settings


class Base(DeclarativeBase):
    """Declarative base. Schema is set per model via ``__table_args__``."""


@lru_cache
def get_engine() -> AsyncEngine:
    settings = get_settings()

    connect_args: dict[str, Any] = {
        # Unqualified names resolve inside our own schema; "public" stays on the
        # path for extensions such as pgcrypto's gen_random_uuid().
        "server_settings": {"search_path": f"{settings.db_schema},public"},
    }
    if settings.db_disable_statement_cache:
        connect_args["statement_cache_size"] = 0

    return create_async_engine(
        settings.database_url,
        echo=settings.debug,
        pool_size=settings.db_pool_size,
        max_overflow=0,  # Supabase free tier caps total connections; five services share it
        pool_pre_ping=True,  # pooler drops idle connections; verify before handing one out
        connect_args=connect_args,
    )


@lru_cache
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), expire_on_commit=False, autoflush=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding one session per request."""
    async with get_sessionmaker()() as session:
        yield session
