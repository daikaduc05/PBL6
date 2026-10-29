from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pbl6_common.errors import register_exception_handlers
from pbl6_common.logging import RequestIdMiddleware, configure_logging

from notification.api.v1.notifications import router as notifications_router
from notification.config import get_settings
from notification.deps import email_service, engine, session_factory
from notification.scheduler import create_scheduler


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

    yield

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

    # The RabbitMQ consumer (T16) starts from the lifespan handler above once
    # that feature lands.

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
