"""Unit tests for the consumer's retry/DLQ decision logic.

`_process_one` is what `consume_forever` calls per message — pulled out
specifically so this is testable without a real broker. The fakes below
only need to behave like aio_pika's message/channel enough to observe
ack/nack/DLQ-publish calls; `consume_forever`'s own outer loop
(`queue.iterator()`) is real aio_pika machinery and is instead covered by
this project's live Docker+RabbitMQ verification (same approach as the
payment outbox relay, T31).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import pytest
from pbl6_common.events.consumer import _delivery_count, _process_one
from pbl6_common.events.schemas import EventEnvelope


@dataclass
class FakeMessage:
    body: bytes
    headers: dict[str, Any] | None = field(default_factory=dict)
    content_type: str | None = "application/json"
    message_id: str | None = "msg-1"
    acked: bool = False
    nacked_requeue: bool | None = None

    async def ack(self) -> None:
        self.acked = True

    async def nack(self, requeue: bool) -> None:
        self.nacked_requeue = requeue


class FakeDefaultExchange:
    def __init__(self) -> None:
        self.published: list[tuple[object, str]] = []

    async def publish(self, message: object, *, routing_key: str) -> None:
        self.published.append((message, routing_key))


class FakeChannel:
    def __init__(self) -> None:
        self.default_exchange = FakeDefaultExchange()


def valid_envelope_body() -> bytes:
    envelope = EventEnvelope(
        event_id=uuid.uuid4(),
        event_type="payment.succeeded",
        occurred_at=datetime.now(UTC),
        producer="payment-service",
        data={},
    )
    return envelope.model_dump_json().encode("utf-8")


def test_delivery_count_is_zero_on_first_delivery():
    assert _delivery_count(FakeMessage(body=b"{}", headers={})) == 0


def test_delivery_count_is_zero_when_headers_is_none():
    assert _delivery_count(FakeMessage(body=b"{}", headers=None)) == 0


def test_delivery_count_reads_the_first_x_death_entrys_count():
    message = FakeMessage(body=b"{}", headers={"x-death": [{"count": 2, "reason": "rejected"}]})
    assert _delivery_count(message) == 2


@pytest.mark.asyncio
async def test_malformed_body_goes_straight_to_dlq_without_raising():
    """The regression this guards against: a parse failure must not
    propagate out of _process_one, or it kills consume_forever's whole
    loop permanently (found via live testing during T26)."""
    channel = FakeChannel()
    message = FakeMessage(body=b"not json at all")

    async def handler(envelope: EventEnvelope) -> None:
        raise AssertionError("must not be reached for a malformed body")

    await _process_one(channel, message, handler, dlq_name="account.events.dlq", max_deliveries=3)

    assert message.acked is True
    assert message.nacked_requeue is None
    assert len(channel.default_exchange.published) == 1
    assert channel.default_exchange.published[0][1] == "account.events.dlq"


@pytest.mark.asyncio
async def test_successful_handler_just_acks():
    channel = FakeChannel()
    message = FakeMessage(body=valid_envelope_body())
    seen = []

    async def handler(envelope: EventEnvelope) -> None:
        seen.append(envelope)

    await _process_one(channel, message, handler, dlq_name="account.events.dlq", max_deliveries=3)

    assert message.acked is True
    assert len(seen) == 1
    assert channel.default_exchange.published == []


@pytest.mark.asyncio
async def test_handler_failure_below_max_deliveries_nacks_without_requeue():
    channel = FakeChannel()
    message = FakeMessage(body=valid_envelope_body(), headers={})  # 0 prior deliveries

    async def handler(envelope: EventEnvelope) -> None:
        raise RuntimeError("boom")

    await _process_one(channel, message, handler, dlq_name="account.events.dlq", max_deliveries=3)

    assert message.acked is False
    assert message.nacked_requeue is False  # -> queue's DLX -> <queue>.retry, not DLQ yet
    assert channel.default_exchange.published == []


@pytest.mark.asyncio
async def test_handler_failure_at_max_deliveries_moves_to_dlq():
    channel = FakeChannel()
    # x-death count=2 means this is the 3rd delivery attempt.
    message = FakeMessage(body=valid_envelope_body(), headers={"x-death": [{"count": 2}]})

    async def handler(envelope: EventEnvelope) -> None:
        raise RuntimeError("boom")

    await _process_one(channel, message, handler, dlq_name="account.events.dlq", max_deliveries=3)

    assert message.acked is True  # removed from the retry cycle
    assert message.nacked_requeue is None
    assert len(channel.default_exchange.published) == 1
    assert channel.default_exchange.published[0][1] == "account.events.dlq"
