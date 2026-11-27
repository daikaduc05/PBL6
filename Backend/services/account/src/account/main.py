import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import aio_pika
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from pbl6_common.errors import register_exception_handlers
from pbl6_common.events import consume_forever, declare_consumer_topology, get_exchange
from pbl6_common.logging import RequestIdMiddleware, configure_logging

from account.api.internal import router as internal_router
from account.api.v1.admin_editors import router as admin_editors_router
from account.api.v1.admin_users import router as admin_users_router
from account.api.v1.auth import router as auth_router
from account.api.v1.users import router as users_router
from account.config import get_settings
from account.deps import engine, get_event_publisher, session_factory, set_exchange
from account.events.consumer_wiring import QUEUE_NAME, ROUTING_KEYS, make_payment_succeeded_handler
from account.outbox.relay import relay_once
from account.repositories.outbox_repository import OutboxRepository
from account.repositories.user_repository import UserRepository
from account.services.vip_expiry_service import VipExpiryService

logger = logging.getLogger(__name__)


async def _vip_expiry_tick() -> None:
    async with session_factory() as session:
        service = VipExpiryService(
            users=UserRepository(session),
            publisher=get_event_publisher(session),
        )
        revoked = await service.sweep()
        await session.commit()
        if revoked:
            logger.info("vip expiry sweep: revoked VIP for %d user(s)", revoked)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    connection = None
    consumer_task = None
    exchange = None

    try:
        connection = await aio_pika.connect_robust(settings.rabbitmq_url, timeout=5)
        exchange = await get_exchange(connection)
        set_exchange(exchange)

        channel, queue = await declare_consumer_topology(
            connection, queue_name=QUEUE_NAME, routing_keys=ROUTING_KEYS
        )
        handler = make_payment_succeeded_handler(session_factory)
        consumer_task = asyncio.create_task(consume_forever(channel, queue, handler))
    except Exception:
        logger.exception("account events: RabbitMQ unavailable at startup, relay/consumer disabled")

    scheduler = AsyncIOScheduler()
    scheduler.add_job(_vip_expiry_tick, "cron", hour=0, minute=0, id="vip-expiry-sweep")

    if exchange is not None:
        from pbl6_common.events import publish_envelope

        async def _outbox_tick() -> None:
            async with session_factory() as session:
                repo = OutboxRepository(session)
                published = await relay_once(repo, lambda env: publish_envelope(exchange, env))
                await session.commit()
                if published:
                    logger.info("account outbox relay: published %d event(s)", published)

        scheduler.add_job(
            _outbox_tick, "interval", seconds=5, id="account-outbox-relay", max_instances=1
        )

    scheduler.start()

    yield

    scheduler.shutdown(wait=False)
    if consumer_task is not None:
        consumer_task.cancel()
    if connection is not None:
        await connection.close()


def create_app() -> FastAPI:
    configure_logging(get_settings().log_level)

    app = FastAPI(title="Account Service", version="0.1.0", lifespan=lifespan)
    app.add_middleware(RequestIdMiddleware)
    register_exception_handlers(app)

    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(users_router, prefix="/api/v1")
    app.include_router(admin_users_router, prefix="/api/v1")
    app.include_router(admin_editors_router, prefix="/api/v1")
    app.include_router(internal_router)

    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/docs")

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
