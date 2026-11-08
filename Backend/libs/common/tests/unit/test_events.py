"""Unit tests for the shared event envelope + publish-side plumbing
(backend.md §6). `exchange` is a tiny fake — no real RabbitMQ connection,
which is the point: this only checks that publish_envelope builds the
message correctly and uses event_type as the routing key."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

import pytest
from pbl6_common.events.publisher import publish_envelope
from pbl6_common.events.schemas import EventEnvelope


class FakeExchange:
    def __init__(self) -> None:
        self.published: list[tuple[object, str]] = []

    async def publish(self, message: object, *, routing_key: str) -> None:
        self.published.append((message, routing_key))


def make_envelope(**overrides: object) -> EventEnvelope:
    defaults: dict[str, object] = {
        "event_id": uuid.uuid4(),
        "event_type": "payment.succeeded",
        "occurred_at": datetime.now(UTC),
        "producer": "payment-service",
        "data": {"transaction_id": str(uuid.uuid4())},
    }
    defaults.update(overrides)
    return EventEnvelope(**defaults)  # type: ignore[arg-type]


def test_envelope_defaults_version_to_1():
    envelope = make_envelope()
    assert envelope.version == 1


@pytest.mark.asyncio
async def test_publish_envelope_uses_event_type_as_routing_key():
    exchange = FakeExchange()
    envelope = make_envelope(event_type="payment.failed")

    await publish_envelope(exchange, envelope)  # type: ignore[arg-type]

    assert len(exchange.published) == 1
    _, routing_key = exchange.published[0]
    assert routing_key == "payment.failed"


@pytest.mark.asyncio
async def test_publish_envelope_message_body_round_trips_the_envelope():
    exchange = FakeExchange()
    envelope = make_envelope()

    await publish_envelope(exchange, envelope)  # type: ignore[arg-type]

    message, _ = exchange.published[0]
    body = json.loads(message.body.decode("utf-8"))
    assert body["event_id"] == str(envelope.event_id)
    assert body["event_type"] == envelope.event_type
    assert body["data"] == envelope.data
