import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import aio_pika
from fastapi import FastAPI
from pbl6_common.errors import register_exception_handlers
from pbl6_common.events import consume_forever, declare_consumer_topology
from pbl6_common.logging import RequestIdMiddleware, configure_logging

from notification.api.v1.notifications import router as notifications_router
from notification.config import get_settings
from notification.deps import email_service, engine, session_factory
from notification.events.consumer_wiring import QUEUE_NAME, ROUTING_KEYS, make_event_handler
from notification.scheduler import create_scheduler

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()

    scheduler = None
    if settings.reminder_cron_enabled:
        scheduler = create_scheduler(
            session_factory=session_factory,
            email_service=email_service,
            settings=settings,
        )
        scheduler.start()

    # T16: the event consumer. Same trade-off as account's: RabbitMQ being
    # down must not take the API down with it — view/delete/settings keep
    # working, the consumer simply stays off until a restart finds the broker.
    # The durable queue holds anything published meanwhile.
    connection = None
    consumer_task = None
    try:
        connection = await aio_pika.connect_robust(settings.rabbitmq_url, timeout=5)
        channel, queue = await declare_consumer_topology(
            connection, queue_name=QUEUE_NAME, routing_keys=ROUTING_KEYS
        )
        handler = make_event_handler(
            session_factory, email_service, display_timezone=settings.reminder_timezone
        )
        consumer_task = asyncio.create_task(consume_forever(channel, queue, handler))
    except Exception:
        logger.exception("notification events: RabbitMQ unavailable at startup, consumer disabled")

    yield

    if consumer_task is not None:
        consumer_task.cancel()
    if connection is not None:
        await connection.close()
    if scheduler is not None:
        # wait=False: shutdown should not block on a reminder pass that is
        # still mailing people.
        scheduler.shutdown(wait=False)
    await engine.dispose()


def create_app() -> FastAPI:
    configure_logging(get_settings().log_level)

    app = FastAPI(title="Notification Service", version="0.1.0", lifespan=lifespan)
    app.add_middleware(RequestIdMiddleware)
    register_exception_handlers(app)

    app.include_router(notifications_router, prefix="/api/v1")
    # The recommendation router (T17) mounts here too — same service, because
    # it owns no data of its own and would not justify a second container.

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
