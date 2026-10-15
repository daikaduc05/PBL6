"""Unit tests for the outbox relay's pure logic — no RabbitMQ, no database.
`publish` is a plain async fake so we control success/failure per call."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from payment.outbox.relay import relay_once
from payment_fakes import FakeOutboxRepository


@pytest.mark.asyncio
async def test_relay_publishes_unpublished_rows_and_marks_them():
    outbox = FakeOutboxRepository()
    await outbox.create(aggregate_id=uuid.uuid4(), event_type="payment.succeeded", payload={"a": 1})
    await outbox.create(aggregate_id=uuid.uuid4(), event_type="payment.failed", payload={"b": 2})

    seen = []

    async def publish(envelope):
        seen.append(envelope)

    published = await relay_once(outbox, publish)

    assert published == 2
    assert all(e.published_at is not None for e in outbox.entries)
    assert {s.event_type for s in seen} == {"payment.succeeded", "payment.failed"}
    # event_id reuses the outbox row's own id (dedup key for consumers).
    assert {s.event_id for s in seen} == {e.id for e in outbox.entries}


@pytest.mark.asyncio
async def test_relay_leaves_row_unpublished_when_publish_raises():
    outbox = FakeOutboxRepository()
    entry = await outbox.create(
        aggregate_id=uuid.uuid4(), event_type="payment.succeeded", payload={}
    )

    async def failing_publish(envelope):
        raise ConnectionError("broker unreachable")

    published = await relay_once(outbox, failing_publish)

    assert published == 0
    assert entry.published_at is None  # left for the next tick to retry


@pytest.mark.asyncio
async def test_relay_only_publishes_up_to_batch_size():
    outbox = FakeOutboxRepository()
    for _ in range(5):
        await outbox.create(aggregate_id=uuid.uuid4(), event_type="payment.succeeded", payload={})

    async def publish(envelope):
        pass

    published = await relay_once(outbox, publish, batch_size=3)

    assert published == 3
    assert sum(1 for e in outbox.entries if e.published_at is not None) == 3


@pytest.mark.asyncio
async def test_relay_no_unpublished_rows_is_a_noop():
    outbox = FakeOutboxRepository()
    entry = await outbox.create(aggregate_id=uuid.uuid4(), event_type="x", payload={})
    entry.published_at = datetime.now(UTC)

    async def publish(envelope):
        raise AssertionError("should not be called")

    published = await relay_once(outbox, publish)

    assert published == 0
