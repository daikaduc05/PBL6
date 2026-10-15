"""Generic consume-side plumbing for `pbl6.events` (backend.md §6: "Every
consumer binds its own durable queue plus a dead-letter queue `<queue>.dlq`
after 3 failed deliveries").

Retry/DLQ topology (declared by `declare_consumer_topology`):

    pbl6.events (topic exchange)
         |  routing_key
         v
    <queue>            durable, DLX -> <queue>.retry
         |  (nack on handler failure, attempt < MAX_DELIVERIES)
         v
    <queue>.retry      durable, TTL 5s, DLX -> default exchange / <queue>
         |  (TTL expires -> redelivered to <queue> automatically)
         v
    <queue>            (back where it started; x-death count went up by 1)

    <queue>.dlq         durable, terminal — written to manually once a
                         message's accumulated x-death count reaches
                         MAX_DELIVERIES, instead of bouncing it through
                         <queue>.retry again.

The handler owns idempotency (dedupe on `envelope.event_id`) — this module
only owns delivery: ack on success, retry-with-backoff on failure, and
giving up to the DLQ after MAX_DELIVERIES.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any, cast

import aio_pika

from pbl6_common.events.publisher import EXCHANGE_NAME
from pbl6_common.events.schemas import EventEnvelope

logger = logging.getLogger(__name__)

MAX_DELIVERIES = 3
RETRY_TTL_MS = 5000

HandlerFn = Callable[[EventEnvelope], Awaitable[None]]


async def declare_consumer_topology(
    connection: aio_pika.abc.AbstractConnection,
    *,
    queue_name: str,
    routing_keys: list[str],
    retry_ttl_ms: int = RETRY_TTL_MS,
) -> tuple[aio_pika.abc.AbstractChannel, aio_pika.abc.AbstractQueue]:
    channel = await connection.channel()
    exchange = await channel.declare_exchange(
        EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True
    )

    retry_name = f"{queue_name}.retry"
    dlq_name = f"{queue_name}.dlq"

    await channel.declare_queue(
        dlq_name, durable=True
    )  # terminal — only ever written to manually, see _send_to_dlq

    await channel.declare_queue(
        retry_name,
        durable=True,
        arguments={
            "x-message-ttl": retry_ttl_ms,
            "x-dead-letter-exchange": "",
            "x-dead-letter-routing-key": queue_name,
        },
    )

    queue = await channel.declare_queue(
        queue_name,
        durable=True,
        arguments={
            "x-dead-letter-exchange": "",
            "x-dead-letter-routing-key": retry_name,
        },
    )
    for key in routing_keys:
        await queue.bind(exchange, routing_key=key)

    return channel, queue


def _delivery_count(message: aio_pika.abc.AbstractIncomingMessage) -> int:
    """How many times this message has already been dead-lettered (i.e.
    failed and bounced through `<queue>.retry`). 0 on first delivery.

    RabbitMQ always shapes `x-death` as a list of field-tables; aio_pika's
    header type is a much wider union it can't narrow automatically, so
    this cast just states what the broker guarantees.
    """
    headers = message.headers or {}
    x_death = cast("list[dict[str, Any]] | None", headers.get("x-death"))
    if not x_death:
        return 0
    return int(x_death[0].get("count", 0))


async def _send_to_dlq(
    channel: aio_pika.abc.AbstractChannel,
    dlq_name: str,
    message: aio_pika.abc.AbstractIncomingMessage,
) -> None:
    await channel.default_exchange.publish(
        aio_pika.Message(
            body=message.body,
            content_type=message.content_type,
            message_id=message.message_id,
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        ),
        routing_key=dlq_name,
    )


async def _process_one(
    channel: aio_pika.abc.AbstractChannel,
    message: aio_pika.abc.AbstractIncomingMessage,
    handler: HandlerFn,
    *,
    dlq_name: str,
    max_deliveries: int,
) -> None:
    """One message's worth of the consume loop, pulled out of
    `consume_forever` so it's unit-testable with a fake message/channel —
    no real broker needed (see libs/common/tests/unit/test_consumer.py).

    Critically, a message body that doesn't even parse as an EventEnvelope
    must not raise OUT of this function: an uncaught exception in
    `consume_forever`'s loop kills the whole asyncio task permanently (no
    retry, no DLQ, every later message just piles up unacked), which is
    worse than any single bad message. That failure mode is exactly what
    this split + the try/except below guard against."""
    try:
        envelope = EventEnvelope.model_validate_json(message.body)
    except Exception:
        # Will never parse no matter how many times we retry the same
        # bytes — straight to the DLQ, no point bouncing it.
        logger.exception("consumer: malformed message body — moving straight to DLQ")
        await _send_to_dlq(channel, dlq_name, message)
        await message.ack()
        return

    try:
        await handler(envelope)
    except Exception:
        deliveries = _delivery_count(message) + 1
        if deliveries >= max_deliveries:
            logger.exception(
                "consumer: handler failed %d/%d times for %s (%s) — moving to DLQ",
                deliveries,
                max_deliveries,
                envelope.event_id,
                envelope.event_type,
            )
            await _send_to_dlq(channel, dlq_name, message)
            await message.ack()  # removed from the retry cycle; safe in the DLQ now
        else:
            logger.exception(
                "consumer: handler failed (%d/%d) for %s (%s) — will retry",
                deliveries,
                max_deliveries,
                envelope.event_id,
                envelope.event_type,
            )
            await message.nack(requeue=False)  # -> queue's DLX -> <queue>.retry
    else:
        await message.ack()


async def consume_forever(
    channel: aio_pika.abc.AbstractChannel,
    queue: aio_pika.abc.AbstractQueue,
    handler: HandlerFn,
    *,
    max_deliveries: int = MAX_DELIVERIES,
) -> None:
    """Runs until cancelled. One failing message doesn't stop the loop —
    see `_process_one`'s docstring for why that guarantee matters."""
    dlq_name = f"{queue.name}.dlq"
    async with queue.iterator() as messages:
        async for message in messages:
            await _process_one(
                channel, message, handler, dlq_name=dlq_name, max_deliveries=max_deliveries
            )
