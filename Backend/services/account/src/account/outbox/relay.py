"""Outbox relay for Account Service: reads unpublished `account.outbox` rows
and publishes them to RabbitMQ with at-least-once delivery guarantee.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from pbl6_common.events.schemas import EventEnvelope

from account.repositories.outbox_repository import OutboxRepository

logger = logging.getLogger(__name__)

PublishFn = Callable[[EventEnvelope], Awaitable[None]]


async def relay_once(
    repo: OutboxRepository,
    publish: PublishFn,
    *,
    producer: str = "account-service",
    batch_size: int = 20,
) -> int:
    rows = await repo.fetch_unpublished(limit=batch_size)
    published = 0
    for row in rows:
        envelope = EventEnvelope(
            event_id=row.id,
            event_type=row.event_type,
            occurred_at=row.created_at,
            producer=producer,
            data=row.payload,
        )
        try:
            await publish(envelope)
        except Exception:
            logger.exception(
                "account outbox relay: failed to publish %s (%s)", row.id, row.event_type
            )
            continue
        await repo.mark_published(row)
        published += 1
    return published
