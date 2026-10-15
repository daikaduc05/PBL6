from functools import lru_cache

from pbl6_common.config import BaseServiceSettings


class PaymentSettings(BaseServiceSettings):
    """Payment service reads the same env vars as every service, plus:

    mock_payment: real VNPay/Momo integration isn't available yet (no
    working sandbox credentials — see T29's commit for why), so this
    defaults to True. Checkout marks the transaction SUCCESS immediately
    and skips the real gateway round-trip entirely (backend.md's
    documented fallback for exactly this situation).

    vnpay_hash_secret / momo_access_key / momo_secret_key: used by T30's
    webhook signature verification. Placeholder defaults since there's no
    real sandbox account — set real values once one exists.
    """

    mock_payment: bool = True
    checkout_result_url: str = "http://localhost:3000/checkout/result"

    vnpay_hash_secret: str = "change-me-vnpay-hash-secret"
    momo_access_key: str = "change-me-momo-access-key"
    momo_secret_key: str = "change-me-momo-secret-key"


@lru_cache
def get_settings() -> PaymentSettings:
    """Lazy, cached singleton — importing this module must never require env
    vars to be set (e.g. a unit test importing the class for a type hint)."""
    return PaymentSettings()  # type: ignore[call-arg]
