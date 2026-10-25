"""SePay bank-transfer webhook (HMAC-SHA256) + VietQR generation.

Signature scheme copied from a working, already-deployed reference
implementation the project owner provided directly (a NestJS controller,
iap-webhook.controller.ts:112-157), and independently cross-checked
against SePay's own public docs
(developer.sepay.vn/vi/sepay-webhooks/xac-thuc) — both agree exactly.
Confidence here is HIGH, same tier as T30's Momo integration (copied
verbatim from official docs), unlike T30's VNPay branch which was never
verified against a live signature.

Signature = "sha256=" + HMAC-SHA256(secret, f"{timestamp}." + raw_body),
computed over the RAW, un-re-serialized request body bytes — re-encoding
JSON (even losslessly) can change byte-for-byte content (key order,
whitespace) and silently break verification. `timestamp` is Unix seconds;
SePay's own sample rejects anything outside a ±300s window (replay
protection) — see TIMESTAMP_TOLERANCE_SECONDS.

Unlike VNPay/Momo, SePay never calls back with "payment failed" — a bank
transfer either lands (one `transferType: "in"` webhook) or nothing ever
arrives. There is no checkout-time API call either: the QR code the
payer scans is generated entirely client-side (well, server-side here)
from account/bank/amount/content — see build_qr_url. VietQR's `des` field
must be letters/digits only, no diacritics, hence the plain hex encoding
in transfer_content_for.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import time
import uuid
from decimal import Decimal
from urllib.parse import urlencode

TIMESTAMP_TOLERANCE_SECONDS = 300  # ±5 min, per SePay's own PHP sample


def verify_signature(
    raw_body: bytes, *, signature: str | None, timestamp: str | None, secret: str
) -> bool:
    if not signature or not timestamp:
        return False
    try:
        timestamp_seconds = float(timestamp)
    except ValueError:
        return False
    if abs(time.time() - timestamp_seconds) > TIMESTAMP_TOLERANCE_SECONDS:
        return False

    mac = hmac.new(secret.encode("utf-8"), digestmod=hashlib.sha256)
    mac.update(f"{timestamp}.".encode())
    mac.update(raw_body)
    expected = f"sha256={mac.hexdigest()}"

    return hmac.compare_digest(expected, signature)


_CONTENT_PREFIX = "VIP"
_CONTENT_RE = re.compile(rf"{_CONTENT_PREFIX}([0-9a-fA-F]{{32}})")


def transfer_content_for(transaction_id: uuid.UUID) -> str:
    """Letters/digits only (VietQR's own requirement) and globally unique
    since it embeds the transaction's own id — matching an incoming
    webhook back to a transaction is then a plain substring search, no
    separate reference table needed."""
    return f"{_CONTENT_PREFIX}{transaction_id.hex}"


def extract_transaction_id(text: str) -> uuid.UUID | None:
    match = _CONTENT_RE.search(text or "")
    if not match:
        return None
    try:
        return uuid.UUID(match.group(1))
    except ValueError:
        return None


def build_qr_url(*, account_number: str, bank_code: str, amount: Decimal, content: str) -> str:
    """VietQR image endpoint SePay's own docs point to (qr.sepay.vn/docs),
    NOT a sepay.vn domain — only `acc`/`bank` are required there, but we
    always pass `des` (the transfer content we need back) and `amount`
    (so the payer's banking app pre-fills both)."""
    params = {
        "acc": account_number,
        "bank": bank_code,
        "amount": str(int(amount)),
        "des": content,
    }
    return f"https://vietqr.app/img?{urlencode(params)}"
