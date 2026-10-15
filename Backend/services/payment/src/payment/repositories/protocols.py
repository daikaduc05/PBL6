"""Structural (Protocol) types for payment's repositories — service
constructors type-hint against these, not the concrete classes, so a unit
test's fake repository satisfies the check by shape instead of needing to
inherit from it (same pattern as account.repositories.protocols, adopted
there after the T28 mypy lesson)."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any, Protocol

from payment.models.outbox import OutboxEntry
from payment.models.transaction import Transaction


class TransactionRepositoryProtocol(Protocol):
    async def create(
        self, *, user_id: uuid.UUID, amount: Decimal, payment_method: str, plan_code: str
    ) -> Transaction: ...

    async def get_by_id(self, transaction_id: uuid.UUID) -> Transaction | None: ...

    async def save(self, transaction: Transaction) -> None: ...


class OutboxRepositoryProtocol(Protocol):
    async def create(
        self, *, aggregate_id: uuid.UUID, event_type: str, payload: dict[str, Any]
    ) -> OutboxEntry: ...

    async def fetch_unpublished(self, *, limit: int) -> list[OutboxEntry]: ...

    async def mark_published(self, entry: OutboxEntry) -> None: ...
