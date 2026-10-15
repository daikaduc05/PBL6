"""Unit tests: repository is a fake — no database, no network."""

from __future__ import annotations

import hashlib
import hmac
import uuid

import pytest
from payment.config import PaymentSettings
from payment.services.webhook_service import WebhookService
from payment.webhooks import momo, vnpay
from payment_fakes import FakeTransactionRepository
from pbl6_common.errors import UnauthorizedError

VNPAY_SECRET = "test-vnpay-hash-secret"
MOMO_ACCESS_KEY = "test-momo-access-key"
MOMO_SECRET = "test-momo-secret-key"


def make_settings() -> PaymentSettings:
    return PaymentSettings(
        database_url="postgresql+asyncpg://unused/unused",
        jwt_secret="test-secret-test-secret-test-secret",
        vnpay_hash_secret=VNPAY_SECRET,
        momo_access_key=MOMO_ACCESS_KEY,
        momo_secret_key=MOMO_SECRET,
    )


def make_service() -> tuple[WebhookService, FakeTransactionRepository]:
    transactions = FakeTransactionRepository()
    return WebhookService(transactions=transactions, settings=make_settings()), transactions


def signed_vnpay_params(txn_ref: str, **extra: str) -> dict[str, str]:
    params = {
        "vnp_TxnRef": txn_ref,
        "vnp_Amount": "29900000",
        "vnp_ResponseCode": "00",
        "vnp_TransactionNo": "14512345",
        **extra,
    }
    params["vnp_SecureHash"] = vnpay.compute_signature(params, secret=VNPAY_SECRET)
    return params


def signed_momo_payload(order_id: str, **extra: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "partnerCode": "MOMO",
        "orderId": order_id,
        "requestId": "req-1",
        "amount": 299000,
        "orderInfo": "pay with MoMo",
        "orderType": "momo_wallet",
        "transId": 9876543210,
        "resultCode": 0,
        "message": "Success",
        "payType": "qr",
        "responseTime": 1700000000000,
        "extraData": "",
        "callbackToken": "",
        "partnerClientId": "",
        **extra,
    }
    raw = momo._raw_signature_string(payload, momo._IPN_FIELDS, MOMO_ACCESS_KEY)
    payload["signature"] = hmac.new(MOMO_SECRET.encode(), raw.encode(), hashlib.sha256).hexdigest()
    return payload


@pytest.mark.asyncio
async def test_vnpay_valid_webhook_marks_transaction_success():
    service, txns = make_service()
    transaction = txns.seed(status="PENDING")

    ack = await service.handle_vnpay(signed_vnpay_params(str(transaction.id)))

    assert ack["RspCode"] == "00"
    assert txns._by_id[transaction.id].status == "SUCCESS"
    assert txns._by_id[transaction.id].provider_txn_ref == "14512345"


@pytest.mark.asyncio
async def test_vnpay_failed_payment_marks_transaction_failed():
    service, txns = make_service()
    transaction = txns.seed(status="PENDING")

    await service.handle_vnpay(signed_vnpay_params(str(transaction.id), vnp_ResponseCode="24"))

    assert txns._by_id[transaction.id].status == "FAILED"


@pytest.mark.asyncio
async def test_vnpay_invalid_signature_raises():
    service, txns = make_service()
    transaction = txns.seed(status="PENDING")
    params = signed_vnpay_params(str(transaction.id))
    params["vnp_Amount"] = "1"  # tamper after signing

    with pytest.raises(UnauthorizedError):
        await service.handle_vnpay(params)
    assert txns._by_id[transaction.id].status == "PENDING"  # untouched


@pytest.mark.asyncio
async def test_vnpay_unknown_order_returns_not_found_ack_without_raising():
    service, _ = make_service()
    ack = await service.handle_vnpay(signed_vnpay_params(str(uuid.uuid4())))
    assert ack["RspCode"] == "99"


@pytest.mark.asyncio
async def test_vnpay_redelivered_webhook_is_idempotent():
    service, txns = make_service()
    transaction = txns.seed(status="PENDING")
    params = signed_vnpay_params(str(transaction.id))

    await service.handle_vnpay(params)
    txns._by_id[transaction.id].status = "FAILED"  # prove the 2nd call doesn't touch it again
    ack = await service.handle_vnpay(params)

    assert ack["RspCode"] == "00"
    assert txns._by_id[transaction.id].status == "FAILED"  # untouched by the redelivery


@pytest.mark.asyncio
async def test_momo_valid_webhook_marks_transaction_success():
    service, txns = make_service()
    transaction = txns.seed(status="PENDING")

    ack = await service.handle_momo(signed_momo_payload(str(transaction.id)))

    assert ack["resultCode"] == 0
    assert txns._by_id[transaction.id].status == "SUCCESS"
    assert txns._by_id[transaction.id].provider_txn_ref == "9876543210"


@pytest.mark.asyncio
async def test_momo_invalid_signature_raises():
    service, txns = make_service()
    transaction = txns.seed(status="PENDING")
    payload = signed_momo_payload(str(transaction.id))
    payload["amount"] = 1  # tamper after signing

    with pytest.raises(UnauthorizedError):
        await service.handle_momo(payload)
    assert txns._by_id[transaction.id].status == "PENDING"


@pytest.mark.asyncio
async def test_momo_redelivered_webhook_is_idempotent():
    service, txns = make_service()
    transaction = txns.seed(status="PENDING")
    payload = signed_momo_payload(str(transaction.id))

    await service.handle_momo(payload)
    txns._by_id[transaction.id].status = "FAILED"
    ack = await service.handle_momo(payload)

    assert ack["resultCode"] == 0
    assert txns._by_id[transaction.id].status == "FAILED"
