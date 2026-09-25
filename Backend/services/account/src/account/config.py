from functools import lru_cache

from pbl6_common.config import BaseServiceSettings


class AccountSettings(BaseServiceSettings):
    """Account service reads the same env vars as every service, no extras."""


@lru_cache
def get_settings() -> AccountSettings:
    """Lazy, cached singleton — importing this module must never require env
    vars to be set (e.g. `from account.config import AccountSettings` for a
    type hint in a unit test). Only actually reading settings does."""
    return AccountSettings()  # type: ignore[call-arg]
