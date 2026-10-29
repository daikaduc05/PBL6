"""Service-local dependency wiring: this service's own DB engine/session and
Redis connection, plus factories for the services below. `pbl6_common.deps`
covers the auth dependencies shared across services (get_current_user,
require_role).

`session_factory` is also reused by the payment.succeeded consumer
(account.main's lifespan) — it needs its own session per message,
independent of any HTTP request.

`_exchange` is set once by main.py's lifespan after it connects to
RabbitMQ (None if unreachable at startup — see main.py for why that's
non-fatal). `get_event_publisher` wraps whatever it currently holds; admin
services use it to publish account.locked/account.unlocked (T26)."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import aio_pika
from fastapi import Depends
from pbl6_common.db import make_engine, make_get_db, make_session_factory
from pbl6_common.security import RefreshTokenDenylist
from redis.asyncio import Redis, from_url
from sqlalchemy.ext.asyncio import AsyncSession

from account.config import get_settings
from account.email import SmtpEmailSender
from account.events.publisher import RabbitEventPublisher
from account.repositories.password_reset_repository import PasswordResetRepository
from account.repositories.user_repository import UserRepository
from account.services.admin_editor_service import AdminEditorService
from account.services.admin_user_service import AdminUserService
from account.services.auth_service import AuthService
from account.services.password_reset_service import PasswordResetService
from account.services.user_service import UserService

settings = get_settings()
engine = make_engine(settings.database_url)
session_factory = make_session_factory(engine)
get_db = make_get_db(session_factory)

_redis: Redis = from_url(settings.redis_url, decode_responses=True)

_exchange: aio_pika.abc.AbstractExchange | None = None


def set_exchange(exchange: aio_pika.abc.AbstractExchange | None) -> None:
    global _exchange
    _exchange = exchange


async def get_redis() -> AsyncGenerator[Redis, None]:
    yield _redis


def get_event_publisher() -> RabbitEventPublisher:
    return RabbitEventPublisher(_exchange)


def get_auth_service(
    session: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> AuthService:
    return AuthService(
        users=UserRepository(session),
        denylist=RefreshTokenDenylist(redis),
        settings=settings,
    )


def get_user_service(session: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(users=UserRepository(session))


def get_admin_user_service(
    session: AsyncSession = Depends(get_db),
    publisher: RabbitEventPublisher = Depends(get_event_publisher),
) -> AdminUserService:
    return AdminUserService(users=UserRepository(session), publisher=publisher)


def get_admin_editor_service(
    session: AsyncSession = Depends(get_db),
    publisher: RabbitEventPublisher = Depends(get_event_publisher),
) -> AdminEditorService:
    return AdminEditorService(users=UserRepository(session), publisher=publisher)


def get_password_reset_service(session: AsyncSession = Depends(get_db)) -> PasswordResetService:
    return PasswordResetService(
        users=UserRepository(session),
        tokens=PasswordResetRepository(session),
        email_sender=SmtpEmailSender(settings),
        settings=settings,
    )
