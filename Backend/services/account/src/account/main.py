from account.api.v1.auth import router as auth_router
from account.config import get_settings
from account.deps import engine
from fastapi import FastAPI
from pbl6_common.errors import register_exception_handlers
from pbl6_common.logging import RequestIdMiddleware, configure_logging


def create_app() -> FastAPI:
    configure_logging(get_settings().log_level)

    app = FastAPI(title="Account Service", version="0.1.0")
    app.add_middleware(RequestIdMiddleware)
    register_exception_handlers(app)

    app.include_router(auth_router, prefix="/api/v1")

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
