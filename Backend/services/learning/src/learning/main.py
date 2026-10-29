from fastapi import FastAPI
from learning.api.internal import router as internal_router
from learning.api.v1.learning import router as learning_router
from learning.api.v1.quizzes import router as quizzes_router
from learning.config import get_settings
from learning.deps import engine
from pbl6_common.errors import register_exception_handlers
from pbl6_common.logging import RequestIdMiddleware, configure_logging


def create_app() -> FastAPI:
    configure_logging(get_settings().log_level)

    app = FastAPI(title="Learning Service", version="0.1.0")
    app.add_middleware(RequestIdMiddleware)
    register_exception_handlers(app)

    app.include_router(quizzes_router, prefix="/api/v1")
    app.include_router(learning_router, prefix="/api/v1")
    app.include_router(internal_router)

    @app.get("/health")
    async def health():
        return {"status": "ok", "service": "learning"}

    @app.get("/health/ready")
    async def health_ready():
        from sqlalchemy import text

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok"}

    return app


app = create_app()
