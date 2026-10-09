"""Service configuration. Every value comes from the environment."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Service ---
    app_name: str = "notification-service"
    port: int = 8005
    debug: bool = False

    # --- Database: shared Supabase project, this service owns schema "notification" ---
    database_url: str
    db_schema: str = "notification"
    db_pool_size: int = 5

    # The Supabase pooler runs pgbouncer in transaction mode, which reuses a
    # server connection across clients. asyncpg's prepared statements are
    # per-connection, so they collide and raise DuplicatePreparedStatementError
    # at random. Disabling the statement cache is the documented workaround.
    db_disable_statement_cache: bool = True

    # --- Cross-schema reads (spec §0.4) ---
    # Read-only SELECTs against account / content / learning, isolated in
    # readers.py. Flip to false once the internal HTTP endpoints exist.
    allow_cross_schema_read: bool = True

    # --- Messaging / cache (used from T16 onwards) ---
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    redis_url: str = "redis://localhost:6379/0"

    # --- Email (T15) ---
    email_provider: Literal["smtp", "resend"] = "smtp"
    email_from: str = "no-reply@pbl6.dev"
    email_api_key: str = ""
    smtp_host: str = "localhost"
    smtp_port: int = 1025

    # --- Study reminder (T14) ---
    reminder_cron_enabled: bool = True
    reminder_hour: int = 20
    reminder_timezone: str = "Asia/Ho_Chi_Minh"

    # --- Recommendation tuning (T17) ---
    # highest_score is a bare double in learning.histories; the scale is assumed
    # to be 0-100 pending Hà's confirmation (spec §B.1). Changing the scale here
    # rescales the two thresholds below without touching the algorithm.
    reco_score_scale: float = 100.0
    reco_promote_score: float = 80.0
    reco_review_score: float = 50.0
    reco_cache_ttl_seconds: int = 900


@lru_cache
def get_settings() -> Settings:
    """Cached accessor.

    Settings are read lazily rather than at import time so that importing any
    module of this package does not require a populated environment — tests and
    `ruff`/`mypy` runs would otherwise fail on a missing DATABASE_URL.
    """
    return Settings()  # type: ignore[call-arg]  # values come from env
