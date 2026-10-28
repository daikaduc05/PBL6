"""T31 — outbox relay: reads unpublished `payment.outbox` rows and puts
them on RabbitMQ.

At-least-once, not exactly-once: a row only gets `published_at` set after
its publish call returns without raising. If the broker is unreachable, or
the process dies between a successful publish and the `mark_published`
flush, the row is simply retried on the next tick — which means the SAME
event can be delivered twice. That's fine because the row's own `id` is
reused as the envelope's `event_id` on every attempt (see
payment.deps/payment.main), so a redelivery carries the exact same
event_id a consumer already dedupes on (backend.md §6: "consumers must be
idempotent, dedupe on event_id"; notification service's `processed_events`
is keyed on exactly this).

`publish` is injected rather than hardcoded to aio_pika here so this
function is testable with a fake — see tests/unit/test_relay.py.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from pbl6_common.events.schemas import EventEnvelope

from payment.repositories.protocols import OutboxRepositoryProtocol

logger = logging.getLogger(__name__)

PublishFn = Callable[[EventEnvelope], Awaitable[None]]


async def relay_once(
    repo: OutboxRepositoryProtocol,
    publish: PublishFn,
    *,
    producer: str = "payment-service",
    batch_size: int = 20,
) -> int:
    """Publishes up to `batch_size` unpublished rows. Returns how many
    actually got published (a row that fails to publish is left unpublished
    and simply isn't counted — no exception propagates from here)."""
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
            logger.exception("outbox relay: failed to publish %s (%s)", row.id, row.event_type)
            continue
        await repo.mark_published(row)
        published += 1
    return published
