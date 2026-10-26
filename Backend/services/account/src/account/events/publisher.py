"""Direct, best-effort publish for `account.locked` / `account.unlocked`
(T26).

Unlike payment, account doesn't use an outbox here: backend.md scopes the
outbox guarantee to payment specifically (§1 — "Outbox pattern in
payment"), and these two events only feed notification's audit trail, not
a money/VIP-critical state transition. If RabbitMQ is briefly unreachable,
the admin action itself still succeeds; the event is simply dropped rather
than retried, which is an accepted trade-off for this event pair.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any, Protocol

import aio_pika
from pbl6_common.events import EventEnvelope, publish_envelope

logger = logging.getLogger(__name__)

PRODUCER = "account-service"


class EventPublisherProtocol(Protocol):
    async def publish(self, event_type: str, data: dict[str, Any]) -> None: ...


class RabbitEventPublisher:
    def __init__(self, exchange: aio_pika.abc.AbstractExchange | None):
        self._exchange = exchange

    async def publish(self, event_type: str, data: dict[str, Any]) -> None:
        if self._exchange is None:
            logger.warning("event publish skipped (RabbitMQ unavailable): %s", event_type)
            return
        envelope = EventEnvelope(
            event_id=uuid.uuid4(),
            event_type=event_type,
            occurred_at=datetime.now(UTC),
            producer=PRODUCER,
            data=data,
        )
        try:
            await publish_envelope(self._exchange, envelope)
        except Exception:
            logger.exception("event publish failed: %s", event_type)
