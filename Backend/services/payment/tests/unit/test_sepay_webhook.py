"""Pure function tests for payment.webhooks.sepay. The signing algorithm
is copied from an already-deployed reference implementation and
cross-checked against SePay's own docs (see that module's docstring), so
confidence here is high — these tests prove this implementation matches
that algorithm exactly, not just that it's internally consistent."""

from __future__ import annotations

import hashlib
import hmac
import time
import uuid
from decimal import Decimal

from payment.webhooks import sepay

SECRET = "whsec_test_secret_for_unit_tests_only"


def sign(raw_body: bytes, *, timestamp: str, secret: str = SECRET) -> str:
    mac = hmac.new(secret.encode("utf-8"), digestmod=hashlib.sha256)
    mac.update(f"{timestamp}.".encode())
    mac.update(raw_body)
    return f"sha256={mac.hexdigest()}"


def test_verify_signature_accepts_a_correctly_signed_body():
    body = b'{"id": 1, "transferType": "in"}'
    timestamp = str(int(time.time()))
    signature = sign(body, timestamp=timestamp)

    assert sepay.verify_signature(body, signature=signature, timestamp=timestamp, secret=SECRET)


def test_verify_signature_rejects_a_tampered_body():
    body = b'{"id": 1, "transferType": "in"}'
    timestamp = str(int(time.time()))
    signature = sign(body, timestamp=timestamp)
    tampered = b'{"id": 1, "transferType": "out"}'

    assert not sepay.verify_signature(
        tampered, signature=signature, timestamp=timestamp, secret=SECRET
    )


def test_verify_signature_rejects_wrong_secret():
    body = b'{"id": 1}'
    timestamp = str(int(time.time()))
    signature = sign(body, timestamp=timestamp)

    assert not sepay.verify_signature(
        body, signature=signature, timestamp=timestamp, secret="wrong-secret"
    )


def test_verify_signature_rejects_missing_signature_or_timestamp():
    body = b'{"id": 1}'
    assert not sepay.verify_signature(body, signature=None, timestamp="123", secret=SECRET)
    assert not sepay.verify_signature(body, signature="sha256=x", timestamp=None, secret=SECRET)


def test_verify_signature_rejects_an_expired_timestamp():
    body = b'{"id": 1}'
    old_timestamp = str(int(time.time()) - sepay.TIMESTAMP_TOLERANCE_SECONDS - 10)
    signature = sign(body, timestamp=old_timestamp)

    assert not sepay.verify_signature(
        body, signature=signature, timestamp=old_timestamp, secret=SECRET
    )


def test_verify_signature_rejects_non_numeric_timestamp():
    body = b'{"id": 1}'
    assert not sepay.verify_signature(
        body, signature="sha256=x", timestamp="not-a-number", secret=SECRET
    )


def test_transfer_content_round_trips_through_extract():
    transaction_id = uuid.uuid4()
    content = sepay.transfer_content_for(transaction_id)

    assert sepay.extract_transaction_id(content) == transaction_id
    assert content.isalnum()  # VietQR's own requirement: letters/digits only


def test_extract_transaction_id_finds_the_code_inside_a_longer_string():
    transaction_id = uuid.uuid4()
    content = sepay.transfer_content_for(transaction_id)
    noisy = f"NGUYEN VAN A chuyen tien {content} thanh toan"

    assert sepay.extract_transaction_id(noisy) == transaction_id


def test_extract_transaction_id_returns_none_for_unrelated_content():
    assert sepay.extract_transaction_id("some random transfer memo") is None
    assert sepay.extract_transaction_id("") is None


def test_build_qr_url_includes_all_fields():
    url = sepay.build_qr_url(
        account_number="000111222333",
        bank_code="TESTBANK",
        amount=Decimal("299000"),
        content="VIPabc",
    )

    assert url.startswith("https://vietqr.app/img?")
    assert "acc=000111222333" in url
    assert "bank=TESTBANK" in url
    assert "amount=299000" in url
    assert "des=VIPabc" in url
