"""Outbox-backed EventPublisher for `account.locked`, `account.unlocked`,
and `vip.expired`.

When an OutboxRepository is provided (all production HTTP/cron flows),
`publish()` writes an `account.outbox` row in the same database transaction
as the `account.users` update, guaranteeing zero event loss if RabbitMQ is
temporarily down. A background relay (`account.outbox.relay`) flushes the
outbox to RabbitMQ every 5 seconds.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any, Protocol

import aio_pika
from pbl6_common.events import EventEnvelope, publish_envelope

from account.repositories.outbox_repository import OutboxRepository

logger = logging.getLogger(__name__)

PRODUCER = "account-service"


class EventPublisherProtocol(Protocol):
    async def publish(self, event_type: str, data: dict[str, Any]) -> None: ...


class RabbitEventPublisher:
    def __init__(
        self,
        exchange: aio_pika.abc.AbstractExchange | None,
        outbox: OutboxRepository | None = None,
    ):
        self._exchange = exchange
        self._outbox = outbox

    async def publish(self, event_type: str, data: dict[str, Any]) -> None:
        if self._outbox is not None:
            raw_id = data.get("user_id")
            try:
                aggregate_id = uuid.UUID(str(raw_id)) if raw_id else uuid.uuid4()
            except ValueError:
                aggregate_id = uuid.uuid4()
            await self._outbox.create(
                aggregate_id=aggregate_id,
                event_type=event_type,
                payload=data,
            )
            return

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
