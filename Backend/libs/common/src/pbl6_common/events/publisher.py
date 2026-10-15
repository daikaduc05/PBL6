"""Generic publish-side plumbing for the `pbl6.events` exchange
(backend.md §6: topic, durable; routing key == event_type).

Deliberately thin: a service's own outbox/relay code owns retry and
at-least-once semantics (see payment.outbox.relay). This module only knows
how to declare the shared exchange and put one already-built envelope on
the wire.
"""

from __future__ import annotations

import aio_pika

from pbl6_common.events.schemas import EventEnvelope

EXCHANGE_NAME = "pbl6.events"


async def get_exchange(
    connection: aio_pika.abc.AbstractConnection,
) -> aio_pika.abc.AbstractExchange:
    channel = await connection.channel()
    return await channel.declare_exchange(EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True)


async def publish_envelope(
    exchange: aio_pika.abc.AbstractExchange, envelope: EventEnvelope
) -> None:
    message = aio_pika.Message(
        body=envelope.model_dump_json().encode("utf-8"),
        content_type="application/json",
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        message_id=str(envelope.event_id),
    )
    await exchange.publish(message, routing_key=envelope.event_type)
