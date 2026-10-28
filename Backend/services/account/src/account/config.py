from functools import lru_cache

from pbl6_common.config import BaseServiceSettings


class AccountSettings(BaseServiceSettings):
    """Account service reads the same env vars as every service, plus:

    smtp_*: real Gmail SMTP credentials for sending password-reset emails
    (smtp.gmail.com:587, an "App Password" — not the account's real
    password). Placeholder defaults so importing this module never
    requires env vars; real values live only in .env.

    frontend_base_url: used to build the reset link emailed to the user
    (`{frontend_base_url}/reset-password?token=...`). There's no gateway
    yet (T08/T09) so this points at the Next.js app directly.
    """

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = "change-me@example.com"
    smtp_password: str = "change-me-smtp-app-password"
    smtp_from_name: str = "English Self-Study"

    frontend_base_url: str = "http://localhost:3000"


@lru_cache
def get_settings() -> AccountSettings:
    """Lazy, cached singleton — importing this module must never require env
    vars to be set (e.g. `from account.config import AccountSettings` for a
    type hint in a unit test). Only actually reading settings does."""
    return AccountSettings()  # type: ignore[call-arg]
