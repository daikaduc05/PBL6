from functools import lru_cache

from pbl6_common.config import BaseServiceSettings


class PaymentSettings(BaseServiceSettings):
    """Payment service reads the same env vars as every service, no extras."""


@lru_cache
def get_settings() -> PaymentSettings:
    """Lazy, cached singleton — importing this module must never require env
    vars to be set (e.g. a unit test importing the class for a type hint)."""
    return PaymentSettings()  # type: ignore[call-arg]
