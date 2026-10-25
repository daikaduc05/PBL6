from functools import lru_cache
from typing import Literal

from pbl6_common.config import BaseServiceSettings


class NotificationSettings(BaseServiceSettings):
    """Shared env vars (database_url, redis_url, rabbitmq_url, jwt_*) plus the
    ones only M2 needs."""

    # --- Study reminder (T14, function 8.1) ---
    reminder_cron_enabled: bool = True
    reminder_hour: int = 20
    reminder_timezone: str = "Asia/Ho_Chi_Minh"

    # --- Email (T15, function 8.1) ---
    # "smtp" covers both Mailpit in development and Gmail in a demo; "resend"
    # swaps the transport without touching any calling code.
    email_provider: Literal["smtp", "resend"] = "smtp"
    email_from: str = "PBL6 <no-reply@pbl6.dev>"
    email_api_key: str = ""  # resend only

    smtp_host: str = "localhost"
    smtp_port: int = 1025
    # Mailpit needs neither credentials nor TLS; Gmail needs both plus an
    # app password (a normal account password will not authenticate).
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = False

    # Base URL the email buttons link back to.
    app_url: str = "http://localhost:3000"

    # --- Recommendation (T17) ---
    # learning.histories.highest_score is a bare double; a 0-100 scale is
    # assumed pending Hà's confirmation (notif_spec §B.1), so the thresholds
    # stay configurable rather than hardcoded.
    reco_score_scale: float = 100.0
    reco_promote_score: float = 80.0
    reco_review_score: float = 50.0
    reco_cache_ttl_seconds: int = 900


@lru_cache
def get_settings() -> NotificationSettings:
    """Lazy, cached singleton — importing a module must never require env vars
    to be set, only actually reading settings does."""
    return NotificationSettings()  # type: ignore[call-arg]
