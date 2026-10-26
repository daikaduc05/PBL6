"""Database queries only — never raises an HTTP exception (backend.md §3
layering rule: api -> services -> repositories -> models).

`already_processed` + `mark_processed` are used together inside ONE DB
transaction by VipGrantService: check first (cheap read), and if not
processed, the INSERT in `mark_processed` is what actually enforces
idempotency against a race (two deliveries at once) via the primary key —
see VipGrantService's docstring.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from account.models.processed_event import ProcessedEvent


class ProcessedEventRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def already_processed(self, event_id: uuid.UUID) -> bool:
        return await self._session.get(ProcessedEvent, event_id) is not None

    async def mark_processed(self, *, event_id: uuid.UUID, event_type: str) -> None:
        self._session.add(ProcessedEvent(event_id=event_id, event_type=event_type))
        await self._session.flush()
