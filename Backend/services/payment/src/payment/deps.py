"""Service-local dependency wiring: this service's own DB engine/session,
plus factories for CheckoutService/WebhookService. `pbl6_common.deps`
covers the auth dependencies shared across services (get_current_user,
require_role).

`session_factory` is also reused by the outbox relay job (payment.main's
lifespan) — it needs its own session per tick, independent of any HTTP
request."""

from __future__ import annotations

from fastapi import Depends
from pbl6_common.db import make_engine, make_get_db, make_session_factory
from sqlalchemy.ext.asyncio import AsyncSession

from payment.config import get_settings
from payment.repositories.outbox_repository import OutboxRepository
from payment.repositories.transaction_repository import TransactionRepository
from payment.services.checkout_service import CheckoutService
from payment.services.webhook_service import WebhookService

settings = get_settings()
engine = make_engine(settings.database_url)
session_factory = make_session_factory(engine)
get_db = make_get_db(session_factory)


def get_checkout_service(session: AsyncSession = Depends(get_db)) -> CheckoutService:
    return CheckoutService(
        transactions=TransactionRepository(session),
        outbox=OutboxRepository(session),
        settings=settings,
    )


def get_webhook_service(session: AsyncSession = Depends(get_db)) -> WebhookService:
    return WebhookService(
        transactions=TransactionRepository(session),
        outbox=OutboxRepository(session),
        settings=settings,
    )
