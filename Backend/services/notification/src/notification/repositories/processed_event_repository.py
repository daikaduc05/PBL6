"""Database queries only — never raises an HTTP exception (backend.md §3
layering rule: api -> services -> repositories -> models).

Same contract as account's ProcessedEventRepository: `already_processed` is
the cheap early exit for the common redelivery case, but the INSERT inside
`mark_processed` is what actually guarantees exactly-once application — two
concurrent deliveries of the same event both pass the check, and the loser's
insert then hits the primary key, rolling back its whole transaction
(including the duplicate notification written alongside it).
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from notification.models.processed_event import ProcessedEvent


class ProcessedEventRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def already_processed(self, event_id: uuid.UUID) -> bool:
        return await self._session.get(ProcessedEvent, event_id) is not None

    async def mark_processed(self, *, event_id: uuid.UUID, event_type: str) -> None:
        self._session.add(ProcessedEvent(event_id=event_id, event_type=event_type))
        await self._session.flush()
