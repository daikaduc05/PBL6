"""Database queries only — never raises an HTTP exception (backend.md §3
layering rule: api -> services -> repositories -> models)."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from payment.models.transaction import Transaction


class TransactionRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self, *, user_id: uuid.UUID, amount: Decimal, payment_method: str, plan_code: str
    ) -> Transaction:
        transaction = Transaction(
            user_id=user_id,
            amount=amount,
            payment_method=payment_method,
            plan_code=plan_code,
            status="PENDING",
        )
        self._session.add(transaction)
        await self._session.flush()
        return transaction

    async def get_by_id(self, transaction_id: uuid.UUID) -> Transaction | None:
        return await self._session.get(Transaction, transaction_id)

    async def save(self, transaction: Transaction) -> None:
        """Persists in-place mutations on an already-loaded Transaction."""
        await self._session.flush()
