"""T16 — events from other services become notifications (function 8.2).

Fakes over protocols, same style as test_reminder_service: these are the
business rules (dedupe, translation, failure classification), which need no
broker and no database to be exercised.
"""

import uuid
from datetime import UTC, datetime

import pytest
from notification.events.handler import (
    EmailPlan,
    EventHandlerService,
    MalformedEventError,
)
from notification.models.message import MessageType
from notification.repositories.external_reader import ActiveUser
from pbl6_common.events import EventEnvelope

USER = ActiveUser(id=uuid.uuid4(), email="minh@pbl6.test", full_name="Minh")


class FakeMessages:
    def __init__(self):
        self.created: list[dict] = []

    async def create(self, *, user_id, title, content, type):
        self.created.append({"user_id": user_id, "title": title, "content": content, "type": type})
        return None


class FakeLedger:
    def __init__(self, seen: set[uuid.UUID] | None = None):
        self.seen = seen or set()
        self.marked: list[uuid.UUID] = []

    async def already_processed(self, event_id) -> bool:
        return event_id in self.seen

    async def mark_processed(self, *, event_id, event_type) -> None:
        self.marked.append(event_id)


class FakeUsers:
    def __init__(self, known: list[ActiveUser]):
        self._known = {u.id: u for u in known}

    async def user(self, user_id):
        return self._known.get(user_id)


def build(
    *, seen: set[uuid.UUID] | None = None, users: list[ActiveUser] | None = None
) -> tuple[EventHandlerService, FakeMessages, FakeLedger]:
    messages = FakeMessages()
    ledger = FakeLedger(seen)
    service = EventHandlerService(
        messages=messages,
        ledger=ledger,
        users=FakeUsers(users if users is not None else [USER]),
    )
    return service, messages, ledger


def envelope(event_type: str, data: dict, *, event_id: uuid.UUID | None = None) -> EventEnvelope:
    return EventEnvelope(
        event_id=event_id or uuid.uuid4(),
        event_type=event_type,
        occurred_at=datetime(2026, 11, 8, 7, 30, tzinfo=UTC),
        producer="test",
        data=data,
    )


def payment_data(**overrides) -> dict:
    data = {
        "transaction_id": str(uuid.uuid4()),
        "user_id": str(USER.id),
        "plan_id": "VIP_1_MONTH",
        "amount_vnd": 5000.0,
        "duration_days": 30,
    }
    data.update(overrides)
    return data


# --------------------------------------------------------------------------
# Translation: each event type becomes the right notification
# --------------------------------------------------------------------------


async def test_payment_creates_notification_and_owes_an_email():
    service, messages, _ = build()

    plan = await service.apply(envelope("payment.succeeded", payment_data()))

    row = messages.created[0]
    assert row["user_id"] == USER.id
    assert row["type"] == MessageType.PAYMENT_SUCCEEDED
    assert "5,000" in row["content"]
    assert isinstance(plan, EmailPlan)
    assert plan.to == USER.email
    assert plan.template == "vip_confirmed"
    assert plan.context["plan_name"] == "VIP 1 tháng"


async def test_payment_wording_does_not_promise_instant_vip():
    """Account flips the VIP flag off this same event, possibly seconds later —
    the in-app text must not claim what may not be true yet."""
    service, messages, _ = build()

    await service.apply(envelope("payment.succeeded", payment_data()))

    assert "sẽ được kích hoạt" in messages.created[0]["content"]


async def test_vip_expired_shows_the_local_wall_clock():
    """expired_at arrives as UTC; 17:00 UTC is 24:00 in Hanoi — printing the
    UTC figure would tell the user they expired seven hours earlier."""
    service, messages, _ = build()

    await service.apply(
        envelope(
            "vip.expired",
            {"user_id": str(USER.id), "expired_at": "2026-11-08T17:00:00Z"},
        )
    )

    row = messages.created[0]
    assert row["type"] == MessageType.VIP_EXPIRED
    assert "00:00" in row["content"]  # 17:00 UTC == midnight +07
    assert "09/11/2026" in row["content"]  # and the day rolls over too


async def test_account_locked_includes_the_reason_when_given():
    service, messages, _ = build()

    await service.apply(envelope("account.locked", {"user_id": str(USER.id), "reason": "spam"}))

    row = messages.created[0]
    assert row["type"] == MessageType.ACCOUNT_LOCKED
    assert "spam" in row["content"]


async def test_account_locked_reads_cleanly_without_a_reason():
    service, messages, _ = build()

    await service.apply(envelope("account.locked", {"user_id": str(USER.id)}))

    assert "Lý do" not in messages.created[0]["content"]


async def test_account_unlocked_translates():
    service, messages, _ = build()

    plan = await service.apply(envelope("account.unlocked", {"user_id": str(USER.id)}))

    assert messages.created[0]["type"] == MessageType.ACCOUNT_UNLOCKED
    assert plan is None  # in-app only, no email


# --------------------------------------------------------------------------
# Dedupe: at-least-once delivery must not mean at-least-once notification
# --------------------------------------------------------------------------


async def test_a_redelivered_event_does_nothing():
    event_id = uuid.uuid4()
    service, messages, ledger = build(seen={event_id})

    plan = await service.apply(envelope("payment.succeeded", payment_data(), event_id=event_id))

    assert messages.created == []
    assert ledger.marked == []
    assert plan is None


async def test_a_fresh_event_is_recorded_in_the_ledger():
    event_id = uuid.uuid4()
    service, _, ledger = build()

    await service.apply(envelope("account.unlocked", {"user_id": str(USER.id)}, event_id=event_id))

    assert ledger.marked == [event_id]


# --------------------------------------------------------------------------
# Failure classification
# --------------------------------------------------------------------------


async def test_an_unknown_event_type_is_ignored_not_an_error():
    """Contract rule (backend.md §6): a producer must be able to ship a new
    event type before every consumer has caught up."""
    service, messages, ledger = build()

    plan = await service.apply(envelope("quiz.completed", {"whatever": 1}))

    assert messages.created == []
    assert ledger.marked == []  # not marked: nothing was applied
    assert plan is None


async def test_a_payload_missing_its_user_raises_the_permanent_error():
    """Retrying replays the same bytes, so this must escape to the DLQ path,
    not be acked away silently."""
    service, messages, _ = build()

    with pytest.raises(MalformedEventError):
        await service.apply(envelope("payment.succeeded", payment_data(user_id=None)))

    assert messages.created == []


async def test_a_payload_with_garbage_types_raises_the_permanent_error():
    service, _, _ = build()

    with pytest.raises(MalformedEventError):
        await service.apply(
            envelope("vip.expired", {"user_id": str(USER.id), "expired_at": "yesterday-ish"})
        )


async def test_payment_for_an_invisible_user_still_writes_the_row():
    """The in-app notification has no FK and must survive; only the email is
    impossible without an address."""
    service, messages, ledger = build(users=[])

    plan = await service.apply(envelope("payment.succeeded", payment_data()))

    assert len(messages.created) == 1
    assert len(ledger.marked) == 1
    assert plan is None  # no address -> no email, but nothing raised


# --------------------------------------------------------------------------
# Forward compatibility
# --------------------------------------------------------------------------


async def test_extra_payload_fields_are_tolerated():
    """A producer may add fields without a version bump; old consumers must
    not choke on them."""
    service, messages, _ = build()

    await service.apply(
        envelope("account.unlocked", {"user_id": str(USER.id), "unlocked_by": "admin-7"})
    )

    assert len(messages.created) == 1
