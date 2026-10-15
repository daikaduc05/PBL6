import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import aio_pika
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from pbl6_common.errors import register_exception_handlers
from pbl6_common.events.publisher import get_exchange, publish_envelope
from pbl6_common.logging import RequestIdMiddleware, configure_logging

from payment.api.v1.payments import router as payments_router
from payment.api.v1.webhooks import router as webhooks_router
from payment.config import get_settings
from payment.deps import engine, session_factory
from payment.outbox.relay import relay_once
from payment.repositories.outbox_repository import OutboxRepository

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    connection = None
    scheduler = None

    try:
        connection = await aio_pika.connect_robust(settings.rabbitmq_url, timeout=5)
        exchange = await get_exchange(connection)

        async def tick() -> None:
            async with session_factory() as session:
                repo = OutboxRepository(session)
                published = await relay_once(repo, lambda env: publish_envelope(exchange, env))
                await session.commit()
                if published:
                    logger.info("outbox relay: published %d event(s)", published)

        scheduler = AsyncIOScheduler()
        scheduler.add_job(tick, "interval", seconds=5, id="outbox-relay", max_instances=1)
        scheduler.start()
    except Exception:
        # RabbitMQ not reachable (e.g. local dev without `docker compose up
        # rabbitmq`) shouldn't take down checkout/webhook endpoints — the
        # relay just doesn't run, and rows queue up in payment.outbox until
        # it does.
        logger.exception("outbox relay: RabbitMQ unavailable at startup, relay disabled")

    yield

    if scheduler is not None:
        scheduler.shutdown(wait=False)
    if connection is not None:
        await connection.close()


def create_app() -> FastAPI:
    configure_logging(get_settings().log_level)

    app = FastAPI(title="Payment Service", version="0.1.0", lifespan=lifespan)
    app.add_middleware(RequestIdMiddleware)
    register_exception_handlers(app)

    app.include_router(payments_router, prefix="/api/v1")
    app.include_router(webhooks_router, prefix="/api/v1")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/health/ready")
    async def health_ready():
        from sqlalchemy import text

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok"}

    return app


app = create_app()
