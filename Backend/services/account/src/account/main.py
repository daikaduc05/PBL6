import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import aio_pika
from account.api.v1.admin_editors import router as admin_editors_router
from account.api.v1.admin_users import router as admin_users_router
from account.api.v1.auth import router as auth_router
from account.api.v1.users import router as users_router
from account.config import get_settings
from account.deps import engine, session_factory, set_exchange
from account.events.consumer_wiring import QUEUE_NAME, ROUTING_KEYS, make_payment_succeeded_handler
from fastapi import FastAPI
from pbl6_common.errors import register_exception_handlers
from pbl6_common.events import consume_forever, declare_consumer_topology, get_exchange
from pbl6_common.logging import RequestIdMiddleware, configure_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    connection = None
    consumer_task = None

    try:
        connection = await aio_pika.connect_robust(settings.rabbitmq_url, timeout=5)
        set_exchange(await get_exchange(connection))

        channel, queue = await declare_consumer_topology(
            connection, queue_name=QUEUE_NAME, routing_keys=ROUTING_KEYS
        )
        handler = make_payment_succeeded_handler(session_factory)
        consumer_task = asyncio.create_task(consume_forever(channel, queue, handler))
    except Exception:
        # RabbitMQ not reachable (e.g. local dev without `docker compose up
        # rabbitmq`) shouldn't take down the rest of the API — publishing
        # account.locked/unlocked is already best-effort (see
        # account.events.publisher), and the payment.succeeded consumer
        # simply doesn't run until a restart finds RabbitMQ reachable.
        logger.exception("account events: RabbitMQ unavailable at startup, disabled")

    yield

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
