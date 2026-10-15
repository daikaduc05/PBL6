"""Unit tests: repository is a fake — no database, no network."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from payment.config import PaymentSettings
from payment.models.transaction import Transaction
from payment.plans import PLANS
from payment.services.checkout_service import CheckoutService, PaymentNotConfiguredError


class FakeTransactionRepository:
    def __init__(self) -> None:
        self._by_id: dict[uuid.UUID, Transaction] = {}

    async def create(
        self, *, user_id: uuid.UUID, amount: Decimal, payment_method: str, plan_code: str
    ) -> Transaction:
        transaction = Transaction(
            id=uuid.uuid4(),
            user_id=user_id,
            amount=amount,
            payment_method=payment_method,
            plan_code=plan_code,
            status="PENDING",
        )
        self._by_id[transaction.id] = transaction
        return transaction

    async def get_by_id(self, transaction_id: uuid.UUID) -> Transaction | None:
        return self._by_id.get(transaction_id)

    async def save(self, transaction: Transaction) -> None:
        self._by_id[transaction.id] = transaction


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
