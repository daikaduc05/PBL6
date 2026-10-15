"""VNPay IPN signature verification.

Algorithm (standard across VNPay's integration guides — HMAC-SHA512 over
the sorted, URL-encoded query string of every `vnp_*` field except the
hash itself): sort all `vnp_*` keys except vnp_SecureHash/vnp_SecureHashType,
urlencode(sorted(items)), HMAC-SHA512 with vnp_HashSecret, compare hex
digest to vnp_SecureHash.

NOT cross-checked against a real VNPay-generated signature — no working
sandbox account was reachable (see T30's commit). If a real account
becomes available, the first real IPN delivery should be used to confirm
this against their live behaviour before relying on it.
"""

from __future__ import annotations

import hashlib
import hmac
from urllib.parse import urlencode

_EXCLUDED = {"vnp_SecureHash", "vnp_SecureHashType"}


def compute_signature(params: dict[str, str], *, secret: str) -> str:
    data = {k: v for k, v in params.items() if k not in _EXCLUDED and v is not None}
    query = urlencode(sorted(data.items()))
    return hmac.new(secret.encode("utf-8"), query.encode("utf-8"), hashlib.sha512).hexdigest()


def verify_signature(params: dict[str, str], *, secret: str) -> bool:
    received = params.get("vnp_SecureHash", "")
    if not received:
        return False
    expected = compute_signature(params, secret=secret)
    return hmac.compare_digest(expected, received.lower())


def build_ack(*, success: bool, message: str) -> dict[str, str]:
    """VNPay's documented IPN response shape — RspCode "00" means "I
    accepted this notification", distinct from the payment's own result."""
    return {"RspCode": "00" if success else "99", "Message": message}
