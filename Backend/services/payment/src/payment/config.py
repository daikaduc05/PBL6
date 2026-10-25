from functools import lru_cache

from pbl6_common.config import BaseServiceSettings


class PaymentSettings(BaseServiceSettings):
    """Payment service reads the same env vars as every service, plus:

    sepay_webhook_secret: HMAC-SHA256 secret for verifying SePay's webhook
    signature (payment.webhooks.sepay.verify_signature). A real secret —
    set only via .env, never committed.

    sepay_account_number / sepay_bank_code: the bank account SePay
    monitors, used to build each checkout's VietQR code. Not a security
    secret (the QR itself displays this to anyone who scans it), but
    still a real person's real bank account number — placeholder
    defaults here too, same as the webhook secret, so it never ends up
    committed; set real values only via .env.
    """

    sepay_webhook_secret: str = "change-me-sepay-webhook-secret"
    sepay_account_number: str = "change-me-sepay-account-number"
    sepay_bank_code: str = "change-me-sepay-bank-code"


@lru_cache
def get_settings() -> PaymentSettings:
    """Lazy, cached singleton — importing this module must never require env
    vars to be set (e.g. a unit test importing the class for a type hint)."""
    return PaymentSettings()  # type: ignore[call-arg]
