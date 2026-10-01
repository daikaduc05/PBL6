from fastapi import FastAPI
from payment.config import get_settings
from pbl6_common.db import make_engine, make_session_factory
from pbl6_common.errors import register_exception_handlers
from pbl6_common.logging import RequestIdMiddleware, configure_logging

settings = get_settings()
engine = make_engine(settings.database_url)
_session_factory = make_session_factory(engine)


def create_app() -> FastAPI:
    configure_logging(settings.log_level)

    app = FastAPI(title="Payment Service", version="0.1.0")
    app.add_middleware(RequestIdMiddleware)
    register_exception_handlers(app)

    # Routers land in T29 (checkout) / T30 (webhook) / T31 (outbox worker).

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
