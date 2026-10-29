"""T14 — who gets reminded at which hour (function 8.1)."""

import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from notification.repositories.external_reader import ActiveUser
from notification.services.reminder_service import (
    STUDY_REMINDER_TITLE,
    ReminderService,
    local_day_start,
)

VN = ZoneInfo("Asia/Ho_Chi_Minh")

EARLY_BIRD = ActiveUser(id=uuid.uuid4(), email="som@pbl6.test", full_name="Sớm")
NIGHT_OWL = ActiveUser(id=uuid.uuid4(), email="khuya@pbl6.test", full_name="Khuya")
NEVER_CONFIGURED = ActiveUser(id=uuid.uuid4(), email="macdinh@pbl6.test", full_name="Mặc định")


class FakeSettingRepo:
    def __init__(self, *, by_hour: dict[int, set[uuid.UUID]], configured: set[uuid.UUID]):
        self._by_hour = by_hour
        self._configured = configured

    async def user_ids_wanting_hour(self, hour: int) -> set[uuid.UUID]:
        return self._by_hour.get(hour, set())

    async def user_ids_with_a_row(self) -> set[uuid.UUID]:
        return self._configured


class FakeMessageRepo:
    def __init__(self, already_reminded: set[uuid.UUID] | None = None):
        self.already_reminded = already_reminded or set()
        self.created: list[tuple[uuid.UUID, str]] = []

    async def user_ids_with_title_since(self, *, title, since) -> set[uuid.UUID]:
        return self.already_reminded

    async def create(self, *, user_id, title, content):
        self.created.append((user_id, title))
        return None


class FakeExternalReader:
    def __init__(self, users: list[ActiveUser], studied: set[uuid.UUID] | None = None):
        self._users = users
        self._studied = studied or set()

    async def active_users(self) -> list[ActiveUser]:
        return self._users

    async def user_ids_studied_since(self, since) -> set[uuid.UUID]:
        return self._studied


class FakeEmail:
    def __init__(self) -> None:
        self.sent: list[str] = []

    async def send(self, *, to, template, context) -> bool:
        self.sent.append(to)
        return True


def build(
    *,
    users: list[ActiveUser],
    by_hour: dict[int, set[uuid.UUID]],
    configured: set[uuid.UUID],
    studied: set[uuid.UUID] | None = None,
    already_reminded: set[uuid.UUID] | None = None,
) -> tuple[ReminderService, FakeMessageRepo, FakeEmail]:
    messages = FakeMessageRepo(already_reminded)
    email = FakeEmail()

    async def no_sleep(_seconds: float) -> None:
        return None

    service = ReminderService(
        messages=messages,
        settings=FakeSettingRepo(by_hour=by_hour, configured=configured),
        external=FakeExternalReader(users, studied),
        email=email,
        sleep=no_sleep,
    )
    return service, messages, email


def at(hour: int) -> tuple[int, datetime]:
    now = datetime(2026, 10, 15, hour, 0, tzinfo=VN)
    return hour, local_day_start(now)


# --------------------------------------------------------------------------
# Picking recipients by hour
# --------------------------------------------------------------------------


async def test_reminds_only_people_who_chose_this_hour():
    service, messages, email = build(
        users=[EARLY_BIRD, NIGHT_OWL],
        by_hour={7: {EARLY_BIRD.id}, 22: {NIGHT_OWL.id}},
        configured={EARLY_BIRD.id, NIGHT_OWL.id},
    )

    hour, day_start = at(7)
    await service.run(hour=hour, day_start=day_start)

    assert [u for u, _ in messages.created] == [EARLY_BIRD.id]
    assert email.sent == [EARLY_BIRD.email]


async def test_the_night_owl_is_reminded_at_their_own_hour():
    service, messages, _ = build(
        users=[EARLY_BIRD, NIGHT_OWL],
        by_hour={7: {EARLY_BIRD.id}, 22: {NIGHT_OWL.id}},
        configured={EARLY_BIRD.id, NIGHT_OWL.id},
    )

    hour, day_start = at(22)
    await service.run(hour=hour, day_start=day_start)

    assert [u for u, _ in messages.created] == [NIGHT_OWL.id]


async def test_nobody_is_reminded_at_an_hour_no_one_chose():
    service, messages, email = build(
        users=[EARLY_BIRD, NIGHT_OWL],
        by_hour={7: {EARLY_BIRD.id}, 22: {NIGHT_OWL.id}},
        configured={EARLY_BIRD.id, NIGHT_OWL.id},
    )

    hour, day_start = at(13)
    run = await service.run(hour=hour, day_start=day_start)

    assert messages.created == []
    assert email.sent == []
    assert run.candidates == 0


# --------------------------------------------------------------------------
# People who never opened the settings screen
# --------------------------------------------------------------------------


async def test_user_without_settings_is_reminded_at_the_default_hour():
    """Most learners never touch settings, so they have no row at all."""
    service, messages, _ = build(
        users=[NEVER_CONFIGURED],
        by_hour={},
        configured=set(),
    )

    hour, day_start = at(20)  # DEFAULT_REMINDER_HOUR
    await service.run(hour=hour, day_start=day_start)

    assert [u for u, _ in messages.created] == [NEVER_CONFIGURED.id]


async def test_user_without_settings_is_not_reminded_at_other_hours():
    service, messages, _ = build(users=[NEVER_CONFIGURED], by_hour={}, configured=set())

    hour, day_start = at(7)
    await service.run(hour=hour, day_start=day_start)

    assert messages.created == []


async def test_moving_away_from_the_default_hour_stops_the_default_reminder():
    """Someone who picked 07:00 must not also be reminded at 20:00."""
    service, messages, _ = build(
        users=[EARLY_BIRD],
        by_hour={7: {EARLY_BIRD.id}},
        configured={EARLY_BIRD.id},
    )

    hour, day_start = at(20)
    await service.run(hour=hour, day_start=day_start)

    assert messages.created == []


async def test_switching_the_reminder_off_silences_every_hour():
    # Has a row (so no default fallback) but appears under no hour.
    service, messages, _ = build(
        users=[EARLY_BIRD],
        by_hour={},
        configured={EARLY_BIRD.id},
    )

    for hour in (7, 20, 22):
        _, day_start = at(hour)
        await service.run(hour=hour, day_start=day_start)

    assert messages.created == []


# --------------------------------------------------------------------------
# Skipping people who do not need a nudge
# --------------------------------------------------------------------------


async def test_skips_someone_who_already_studied_today():
    service, messages, email = build(
        users=[EARLY_BIRD],
        by_hour={7: {EARLY_BIRD.id}},
        configured={EARLY_BIRD.id},
        studied={EARLY_BIRD.id},
    )

    hour, day_start = at(7)
    run = await service.run(hour=hour, day_start=day_start)

    assert messages.created == []
    assert email.sent == []
    assert run.skipped_already_studied == 1


async def test_skips_someone_already_reminded_today():
    """Guards a re-run, or a restart right as the hour ticks over."""
    service, messages, _ = build(
        users=[EARLY_BIRD],
        by_hour={7: {EARLY_BIRD.id}},
        configured={EARLY_BIRD.id},
        already_reminded={EARLY_BIRD.id},
    )

    hour, day_start = at(7)
    run = await service.run(hour=hour, day_start=day_start)

    assert messages.created == []
    assert run.skipped_already_reminded == 1


async def test_the_notification_carries_the_title_the_dedupe_looks_for():
    """If these drift apart, the same person is reminded every hour."""
    service, messages, _ = build(
        users=[EARLY_BIRD], by_hour={7: {EARLY_BIRD.id}}, configured={EARLY_BIRD.id}
    )

    hour, day_start = at(7)
    await service.run(hour=hour, day_start=day_start)

    assert messages.created[0][1] == STUDY_REMINDER_TITLE


# --------------------------------------------------------------------------
# Timezone and batching
# --------------------------------------------------------------------------


@pytest.mark.parametrize("hour", [0, 7, 20, 23])
async def test_day_start_is_local_midnight_whatever_the_hour(hour):
    now = datetime(2026, 10, 15, hour, 30, tzinfo=VN)

    start = local_day_start(now)

    assert (start.hour, start.minute, start.second) == (0, 0, 0)
    assert start.tzinfo is VN  # a UTC midnight would be 07:00 local
    assert start.date() == now.date()


async def test_pauses_between_email_batches():
    """Gmail blocks a sender that fires hundreds of messages back to back."""
    many = [
        ActiveUser(id=uuid.uuid4(), email=f"u{i}@pbl6.test", full_name=f"U{i}") for i in range(5)
    ]
    slept: list[float] = []

    async def record_sleep(seconds: float) -> None:
        slept.append(seconds)

    messages = FakeMessageRepo()
    service = ReminderService(
        messages=messages,
        settings=FakeSettingRepo(by_hour={7: {u.id for u in many}}, configured=set()),
        external=FakeExternalReader(many),
        email=FakeEmail(),
        email_batch_size=2,
        email_batch_pause_seconds=0.5,
        sleep=record_sleep,
    )

    hour, day_start = at(7)
    run = await service.run(hour=hour, day_start=day_start)

    assert run.notified == 5
    # Pauses after #2 and #4, but not after the last one.
    assert slept == [0.5, 0.5]
