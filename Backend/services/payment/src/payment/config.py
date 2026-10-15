from functools import lru_cache

from pbl6_common.config import BaseServiceSettings


class PaymentSettings(BaseServiceSettings):
    """Payment service reads the same env vars as every service, plus:

    mock_payment: real VNPay/Momo integration isn't available yet (no
    working sandbox credentials — see T29's commit for why), so this
    defaults to True. Checkout marks the transaction SUCCESS immediately
    and skips the real gateway round-trip entirely (backend.md's
    documented fallback for exactly this situation).
    """

    mock_payment: bool = True
    checkout_result_url: str = "http://localhost:3000/checkout/result"


@lru_cache
def get_settings() -> PaymentSettings:
    """Lazy, cached singleton — importing this module must never require env
    vars to be set (e.g. a unit test importing the class for a type hint)."""
    return PaymentSettings()  # type: ignore[call-arg]
