"""Structural (Protocol) type for TransactionRepository — service
constructors type-hint against this, not the concrete class, so a unit
test's fake repository satisfies the check by shape instead of needing to
inherit from it (same pattern as account.repositories.protocols, adopted
there after the T28 mypy lesson)."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Protocol

from payment.models.transaction import Transaction


class TransactionRepositoryProtocol(Protocol):
    async def create(
        self, *, user_id: uuid.UUID, amount: Decimal, payment_method: str, plan_code: str
    ) -> Transaction: ...

    async def get_by_id(self, transaction_id: uuid.UUID) -> Transaction | None: ...

    async def save(self, transaction: Transaction) -> None: ...
