"""Unit tests: repository is a fake — no database, no network."""

from __future__ import annotations

import uuid

import pytest
from payment.config import PaymentSettings
from payment.plans import PLANS
from payment.services.checkout_service import CheckoutService, PaymentNotConfiguredError
from payment_fakes import FakeTransactionRepository


def make_settings(*, mock_payment: bool = True) -> PaymentSettings:
    return PaymentSettings(
        database_url="postgresql+asyncpg://unused/unused",
        jwt_secret="test-secret-test-secret-test-secret",
        mock_payment=mock_payment,
    )


def make_service(*, mock_payment: bool = True) -> tuple[CheckoutService, FakeTransactionRepository]:
    transactions = FakeTransactionRepository()
    service = CheckoutService(
        transactions=transactions, settings=make_settings(mock_payment=mock_payment)
    )
    return service, transactions


@pytest.mark.asyncio
async def test_checkout_mock_mode_marks_transaction_success():
    service, _ = make_service()
    user_id = uuid.uuid4()

    transaction = await service.checkout(
        user_id=user_id, plan_code="VIP_1_MONTH", payment_method="VNPAY"
    )

    assert transaction.status == "SUCCESS"
    assert transaction.user_id == user_id
    assert transaction.amount == PLANS["VIP_1_MONTH"]["amount"]
    assert transaction.payment_method == "VNPAY"
    assert transaction.plan_code == "VIP_1_MONTH"


@pytest.mark.asyncio
async def test_checkout_uses_the_right_amount_per_plan():
    service, _ = make_service()

    for plan_code, plan in PLANS.items():
        transaction = await service.checkout(
            user_id=uuid.uuid4(), plan_code=plan_code, payment_method="MOMO"
        )
        assert transaction.amount == plan["amount"]


@pytest.mark.asyncio
async def test_checkout_without_mock_payment_raises():
    service, _ = make_service(mock_payment=False)

    with pytest.raises(PaymentNotConfiguredError):
        await service.checkout(
            user_id=uuid.uuid4(), plan_code="VIP_1_MONTH", payment_method="VNPAY"
        )


@pytest.mark.asyncio
async def test_build_redirect_url_includes_transaction_id_and_status():
    service, _ = make_service()
    transaction = await service.checkout(
        user_id=uuid.uuid4(), plan_code="VIP_1_MONTH", payment_method="VNPAY"
    )

    url = service.build_redirect_url(transaction)

    assert str(transaction.id) in url
    assert "status=success" in url
