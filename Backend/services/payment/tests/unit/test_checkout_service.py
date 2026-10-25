"""Unit tests: repository is a fake — no database, no network."""

from __future__ import annotations

import uuid

import pytest
from payment.config import PaymentSettings
from payment.plans import PLANS
from payment.services.checkout_service import CheckoutService
from payment.webhooks import sepay
from payment_fakes import FakeTransactionRepository


def make_settings() -> PaymentSettings:
    return PaymentSettings(
        database_url="postgresql+asyncpg://unused/unused",
        jwt_secret="test-secret-test-secret-test-secret",
        sepay_account_number="000111222333",
        sepay_bank_code="TESTBANK",
    )


def make_service() -> tuple[CheckoutService, FakeTransactionRepository]:
    transactions = FakeTransactionRepository()
    service = CheckoutService(transactions=transactions, settings=make_settings())
    return service, transactions


@pytest.mark.asyncio
async def test_checkout_creates_a_pending_transaction():
    service, _ = make_service()
    user_id = uuid.uuid4()

    transaction = await service.checkout(user_id=user_id, plan_code="VIP_1_MONTH")

    assert transaction.status == "PENDING"
    assert transaction.user_id == user_id
    assert transaction.amount == PLANS["VIP_1_MONTH"]["amount"]
    assert transaction.payment_method == "SEPAY"
    assert transaction.plan_code == "VIP_1_MONTH"


@pytest.mark.asyncio
async def test_checkout_uses_the_right_amount_per_plan():
    service, _ = make_service()

    for plan_code, plan in PLANS.items():
        transaction = await service.checkout(user_id=uuid.uuid4(), plan_code=plan_code)
        assert transaction.amount == plan["amount"]


@pytest.mark.asyncio
async def test_build_payment_info_embeds_the_transaction_id_in_the_qr_content():
    service, _ = make_service()
    transaction = await service.checkout(user_id=uuid.uuid4(), plan_code="VIP_1_MONTH")

    info = service.build_payment_info(transaction)

    assert info["transfer_content"] == sepay.transfer_content_for(transaction.id)
    assert sepay.extract_transaction_id(info["transfer_content"]) == transaction.id
    assert info["amount"] == transaction.amount
    assert info["bank_account_number"] == "000111222333"
    assert info["bank_code"] == "TESTBANK"


@pytest.mark.asyncio
async def test_build_payment_info_qr_url_carries_account_bank_amount_and_content():
    service, _ = make_service()
    transaction = await service.checkout(user_id=uuid.uuid4(), plan_code="VIP_3_MONTHS")

    info = service.build_payment_info(transaction)

    assert info["qr_code_url"].startswith("https://vietqr.app/img?")
    assert "acc=000111222333" in info["qr_code_url"]
    assert "bank=TESTBANK" in info["qr_code_url"]
    assert info["transfer_content"] in info["qr_code_url"]
