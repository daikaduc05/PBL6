"""Database queries only — never raises an HTTP exception (backend.md §3
layering rule: api -> services -> repositories -> models).

`create()` is called from the SAME session CheckoutService/WebhookService
already hold (see payment.deps), so an outbox row and the `transactions`
status update it describes commit or roll back together — that is the
entire outbox-pattern guarantee, and it falls out of the existing
session-per-request wiring for free.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from payment.models.outbox import OutboxEntry


class OutboxRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self, *, aggregate_id: uuid.UUID, event_type: str, payload: dict[str, Any]
    ) -> OutboxEntry:
        entry = OutboxEntry(aggregate_id=aggregate_id, event_type=event_type, payload=payload)
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def fetch_unpublished(self, *, limit: int) -> list[OutboxEntry]:
        stmt = (
            select(OutboxEntry)
            .where(OutboxEntry.published_at.is_(None))
            .order_by(OutboxEntry.created_at)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def mark_published(self, entry: OutboxEntry) -> None:
        entry.published_at = datetime.now(UTC)
        await self._session.flush()
