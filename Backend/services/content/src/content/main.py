from fastapi import FastAPI
from pbl6_common.errors import register_exception_handlers
from pbl6_common.logging import RequestIdMiddleware, configure_logging

from content.config import get_settings
from content.deps import engine


def create_app() -> FastAPI:
    configure_logging(get_settings().log_level)

    app = FastAPI(title="Content Service", version="0.1.0")
    app.add_middleware(RequestIdMiddleware)
    register_exception_handlers(app)

    from content.api.v1.categories import router as categories_router

    app.include_router(categories_router, prefix="/api/v1")

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
