"""Shared test doubles for payment service unit tests.

One canonical FakeTransactionRepository implementing the FULL Protocol
(payment.repositories.protocols.TransactionRepositoryProtocol) that every
service constructor expects. Account service learned this the hard way in
T28/T30 (four near-duplicate partial fakes, each missing different
methods, broke the moment Protocol typing was introduced) — starting
payment service with one shared, complete fake from the start avoids
repeating that.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from payment.models.transaction import Transaction


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

    def seed(self, **kwargs) -> Transaction:
        transaction = Transaction(
            id=kwargs.pop("id", uuid.uuid4()),
            user_id=kwargs.pop("user_id", uuid.uuid4()),
            amount=kwargs.pop("amount", Decimal("299000")),
            payment_method=kwargs.pop("payment_method", "VNPAY"),
            plan_code=kwargs.pop("plan_code", "VIP_1_MONTH"),
            status=kwargs.pop("status", "PENDING"),
            provider_txn_ref=kwargs.pop("provider_txn_ref", None),
        )
        self._by_id[transaction.id] = transaction
        return transaction
