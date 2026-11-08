"""Unit tests: repositories are fakes — no database, no network."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid

import pytest
from payment.config import PaymentSettings
from payment.services.webhook_service import WebhookService
from payment.webhooks import sepay
from payment_fakes import FakeOutboxRepository, FakeTransactionRepository
from pbl6_common.errors import UnauthorizedError

SECRET = "test-sepay-webhook-secret"


def make_settings() -> PaymentSettings:
    return PaymentSettings(
        database_url="postgresql+asyncpg://unused/unused",
        jwt_secret="test-secret-test-secret-test-secret",
        sepay_webhook_secret=SECRET,
    )


def make_service() -> tuple[WebhookService, FakeTransactionRepository, FakeOutboxRepository]:
    transactions = FakeTransactionRepository()
    outbox = FakeOutboxRepository()
    service = WebhookService(transactions=transactions, outbox=outbox, settings=make_settings())
    return service, transactions, outbox


def sign(body: bytes, *, timestamp: str) -> str:
    mac = hmac.new(SECRET.encode("utf-8"), digestmod=hashlib.sha256)
    mac.update(f"{timestamp}.".encode())
    mac.update(body)
    return f"sha256={mac.hexdigest()}"


def signed_request(payload: dict) -> tuple[bytes, str, str]:
    body = json.dumps(payload).encode("utf-8")
    timestamp = str(int(time.time()))
    return body, sign(body, timestamp=timestamp), timestamp


def sepay_payload(*, content: str, amount: int, **overrides) -> dict:
    payload = {
        "id": 92704,
        "gateway": "Vietinbank",
        "transactionDate": "2026-10-25 09:14:00",
        "accountNumber": "000111222333",
        "subAccount": "",
        "code": None,
        "content": content,
        "transferType": "in",
        "description": content,
        "transferAmount": amount,
        "accumulated": 1250000,
        "referenceCode": "FT26298001234567",
    }
    payload.update(overrides)
    return payload


@pytest.mark.asyncio
async def test_valid_webhook_marks_transaction_success_and_writes_outbox():
    service, txns, outbox = make_service()
    transaction = txns.seed(status="PENDING")
    content = sepay.transfer_content_for(transaction.id)
    body, signature, timestamp = signed_request(
        sepay_payload(content=content, amount=int(transaction.amount))
    )

    ack = await service.handle_sepay(body, signature=signature, timestamp=timestamp)

    assert ack == {"success": True}
    assert txns._by_id[transaction.id].status == "SUCCESS"
    assert txns._by_id[transaction.id].provider_txn_ref == "92704"
    assert len(outbox.entries) == 1
    assert outbox.entries[0].event_type == "payment.succeeded"


@pytest.mark.asyncio
async def test_invalid_signature_raises_and_does_not_touch_the_transaction():
    service, txns, outbox = make_service()
    transaction = txns.seed(status="PENDING")
    content = sepay.transfer_content_for(transaction.id)
    body, signature, timestamp = signed_request(
        sepay_payload(content=content, amount=int(transaction.amount))
    )
    tampered_body = body.replace(b'"in"', b'"out"')  # same length, breaks the signature

    with pytest.raises(UnauthorizedError):
        await service.handle_sepay(tampered_body, signature=signature, timestamp=timestamp)
    assert txns._by_id[transaction.id].status == "PENDING"
    assert outbox.entries == []


@pytest.mark.asyncio
async def test_outgoing_transfer_is_ignored():
    service, txns, outbox = make_service()
    transaction = txns.seed(status="PENDING")
    content = sepay.transfer_content_for(transaction.id)
    body, signature, timestamp = signed_request(
        sepay_payload(content=content, amount=int(transaction.amount), transferType="out")
    )

    ack = await service.handle_sepay(body, signature=signature, timestamp=timestamp)

    assert ack == {"success": True}
    assert txns._by_id[transaction.id].status == "PENDING"
    assert outbox.entries == []


@pytest.mark.asyncio
async def test_content_with_no_recognisable_reference_is_a_noop():
    service, _txns, outbox = make_service()
    body, signature, timestamp = signed_request(
        sepay_payload(content="random transfer memo", amount=100000)
    )

    ack = await service.handle_sepay(body, signature=signature, timestamp=timestamp)

    assert ack == {"success": True}
    assert outbox.entries == []


@pytest.mark.asyncio
async def test_unknown_transaction_id_is_a_noop():
    service, _txns, outbox = make_service()
    content = sepay.transfer_content_for(uuid.uuid4())  # never seeded
    body, signature, timestamp = signed_request(sepay_payload(content=content, amount=299000))

    ack = await service.handle_sepay(body, signature=signature, timestamp=timestamp)

    assert ack == {"success": True}
    assert outbox.entries == []


@pytest.mark.asyncio
async def test_amount_mismatch_does_not_apply():
    service, txns, outbox = make_service()
    transaction = txns.seed(status="PENDING")
    content = sepay.transfer_content_for(transaction.id)
    wrong_amount = int(transaction.amount) + 1000
    body, signature, timestamp = signed_request(sepay_payload(content=content, amount=wrong_amount))

    ack = await service.handle_sepay(body, signature=signature, timestamp=timestamp)

    assert ack == {"success": True}
    assert txns._by_id[transaction.id].status == "PENDING"
    assert outbox.entries == []


@pytest.mark.asyncio
async def test_redelivered_webhook_is_idempotent():
    service, txns, outbox = make_service()
    transaction = txns.seed(status="PENDING")
    content = sepay.transfer_content_for(transaction.id)
    body, signature, timestamp = signed_request(
        sepay_payload(content=content, amount=int(transaction.amount))
    )

    await service.handle_sepay(body, signature=signature, timestamp=timestamp)
    txns._by_id[transaction.id].status = "PENDING"  # prove redelivery doesn't touch it again
    ack = await service.handle_sepay(body, signature=signature, timestamp=timestamp)

    assert ack == {"success": True}
    assert txns._by_id[transaction.id].status == "PENDING"  # untouched by the redelivery
    assert len(outbox.entries) == 1  # no second event


@pytest.mark.asyncio
async def test_reference_found_in_description_when_missing_from_content():
    service, txns, outbox = make_service()
    transaction = txns.seed(status="PENDING")
    content = sepay.transfer_content_for(transaction.id)
    body, signature, timestamp = signed_request(
        sepay_payload(content="unrelated", amount=int(transaction.amount), description=content)
    )

    ack = await service.handle_sepay(body, signature=signature, timestamp=timestamp)

    assert ack == {"success": True}
    assert txns._by_id[transaction.id].status == "SUCCESS"
    assert len(outbox.entries) == 1
