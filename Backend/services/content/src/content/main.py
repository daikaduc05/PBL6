import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import aio_pika
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from pbl6_common.errors import register_exception_handlers
from pbl6_common.events.publisher import get_exchange, publish_envelope
from pbl6_common.logging import RequestIdMiddleware, configure_logging

from content.config import get_settings
from content.deps import engine, session_factory
from content.outbox.relay import relay_once
from content.repositories.outbox_repository import OutboxRepository

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
                    logger.info("content outbox relay: published %d event(s)", published)

        scheduler = AsyncIOScheduler()
        scheduler.add_job(tick, "interval", seconds=5, id="content-outbox-relay", max_instances=1)
        scheduler.start()
    except Exception:
        logger.exception("content outbox relay: RabbitMQ unavailable at startup, relay disabled")

    yield

    if scheduler is not None:
        scheduler.shutdown(wait=False)
    if connection is not None:
        await connection.close()


def create_app() -> FastAPI:
    configure_logging(get_settings().log_level)

    app = FastAPI(title="Content Service", version="0.1.0", lifespan=lifespan)
    app.add_middleware(RequestIdMiddleware)
    register_exception_handlers(app)

    from content.api.v1.categories import router as categories_router
    from content.api.v1.lessons import router as lessons_router
    from content.api.v1.media import router as media_router

    app.include_router(categories_router, prefix="/api/v1")
    app.include_router(lessons_router, prefix="/api/v1")
    app.include_router(media_router, prefix="/api/v1")

    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/docs")

    @app.get("/health")
    async def health():
        return {"status": "ok", "service": "content"}

    @app.get("/health/ready")
    async def health_ready():
        from sqlalchemy import text

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok"}

    return app


app = create_app()
