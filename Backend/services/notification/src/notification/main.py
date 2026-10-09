"""FastAPI application for the notification service (M2)."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, status
from sqlalchemy import text

from notification.config import get_settings
from notification.db import get_engine
from notification.errors import register_exception_handlers, request_id_middleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # The scheduler (T14) and the RabbitMQ consumer (T16) start here once those
    # features land; both are long-lived tasks tied to the app's lifetime.
    yield
    await get_engine().dispose()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="PBL6 Notification Service",
        description=(
            "M2 — in-app messages, email, the 20:00 study reminder, and lesson recommendations."
        ),
        version="0.1.0",
        lifespan=lifespan,
        debug=settings.debug,
    )

    app.middleware("http")(request_id_middleware)
    register_exception_handlers(app)

    @app.get("/health", tags=["health"], summary="Liveness probe")
    async def health() -> dict[str, str]:
        """Process is up. Deliberately touches no dependency."""
        return {"status": "ok", "service": settings.app_name}

    @app.get("/health/ready", tags=["health"], summary="Readiness probe")
    async def health_ready(response: Response) -> dict[str, object]:
        """Dependencies are reachable.

        Only the database is checked for now; RabbitMQ and Redis join this list
        when T16 and the recommendation cache land.
        """
        checks: dict[str, str] = {}
        try:
            async with get_engine().connect() as conn:
                await conn.execute(text("select 1"))
            checks["database"] = "ok"
        except Exception as exc:  # noqa: BLE001 - probe reports, never raises
            checks["database"] = f"error: {type(exc).__name__}"

        ready = all(v == "ok" for v in checks.values())
        if not ready:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "ready" if ready else "not ready", "checks": checks}

    # Routers land here as features merge:
    #   app.include_router(notifications_router)   # T13
    #   app.include_router(recommendation_router)  # T17
    return app


app = create_app()
