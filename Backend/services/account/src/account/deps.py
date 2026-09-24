"""Service-local dependency wiring: this service's own DB engine/session and
Redis connection, plus a factory for AuthService. `pbl6_common.deps` covers
the auth dependencies shared across services (get_current_user, require_role)."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from account.config import get_settings
from account.repositories.user_repository import UserRepository
from account.services.auth_service import AuthService
from fastapi import Depends
from pbl6_common.db import make_engine, make_get_db, make_session_factory
from pbl6_common.security import RefreshTokenDenylist
from redis.asyncio import Redis, from_url
from sqlalchemy.ext.asyncio import AsyncSession

settings = get_settings()
engine = make_engine(settings.database_url)
_session_factory = make_session_factory(engine)
get_db = make_get_db(_session_factory)

_redis: Redis = from_url(settings.redis_url, decode_responses=True)


async def get_redis() -> AsyncGenerator[Redis, None]:
    yield _redis


def get_auth_service(
    session: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> AuthService:
    return AuthService(
        users=UserRepository(session),
        denylist=RefreshTokenDenylist(redis),
        settings=settings,
    )
