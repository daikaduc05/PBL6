"""Unit tests: repositories are fakes — no database, no network."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from account.models.user import User
from account.services.vip_grant_service import VipGrantService


class FakeUserRepository:
    def __init__(self) -> None:
        self._by_id: dict[uuid.UUID, User] = {}

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self._by_id.get(user_id)

    async def save(self, user: User) -> None:
        self._by_id[user.id] = user

    def seed(self, **kwargs) -> User:
        user = User(
            id=kwargs.pop("id", uuid.uuid4()),
            email=kwargs.pop("email", f"{uuid.uuid4()}@vidu.com"),
            password_hash="x",
            full_name=kwargs.pop("full_name", "A B"),
            role=kwargs.pop("role", "CUSTOMER"),
            status=kwargs.pop("status", "ACTIVE"),
            is_vip=kwargs.pop("is_vip", False),
            vip_expired_at=kwargs.pop("vip_expired_at", None),
            created_at=kwargs.pop("created_at", datetime.now(UTC)),
        )
        self._by_id[user.id] = user
        return user


class FakeProcessedEventRepository:
    def __init__(self) -> None:
        self._seen: set[uuid.UUID] = set()

    async def already_processed(self, event_id: uuid.UUID) -> bool:
        return event_id in self._seen

    async def mark_processed(self, *, event_id: uuid.UUID, event_type: str) -> None:
        self._seen.add(event_id)


def make_service() -> tuple[VipGrantService, FakeUserRepository, FakeProcessedEventRepository]:
    users = FakeUserRepository()
    processed = FakeProcessedEventRepository()
    return VipGrantService(users=users, processed_events=processed), users, processed


@pytest.mark.asyncio
async def test_grants_vip_from_now_for_a_non_vip_user():
    service, users, _processed = make_service()
    user = users.seed(is_vip=False)
    before = datetime.now(UTC)

    await service.handle_payment_succeeded(
        event_id=uuid.uuid4(), event_type="payment.succeeded", user_id=user.id, duration_days=30
    )

    assert user.is_vip is True
    assert user.vip_expired_at is not None
    assert before + timedelta(days=29) < user.vip_expired_at < before + timedelta(days=31)


@pytest.mark.asyncio
async def test_extends_expiry_for_a_user_still_vip():
    service, users, _processed = make_service()
    current_expiry = datetime.now(UTC) + timedelta(days=10)
    user = users.seed(is_vip=True, vip_expired_at=current_expiry)

    await service.handle_payment_succeeded(
        event_id=uuid.uuid4(), event_type="payment.succeeded", user_id=user.id, duration_days=30
    )

    assert user.vip_expired_at == current_expiry + timedelta(days=30)


@pytest.mark.asyncio
async def test_treats_an_expired_vip_user_like_a_fresh_grant():
    service, users, _processed = make_service()
    lapsed_expiry = datetime.now(UTC) - timedelta(days=5)
    user = users.seed(is_vip=True, vip_expired_at=lapsed_expiry)
    before = datetime.now(UTC)

    await service.handle_payment_succeeded(
        event_id=uuid.uuid4(), event_type="payment.succeeded", user_id=user.id, duration_days=30
    )

    assert before + timedelta(days=29) < user.vip_expired_at < before + timedelta(days=31)


@pytest.mark.asyncio
async def test_redelivered_event_id_does_not_grant_twice():
    service, users, _processed = make_service()
    user = users.seed(is_vip=False)
    event_id = uuid.uuid4()

    await service.handle_payment_succeeded(
        event_id=event_id, event_type="payment.succeeded", user_id=user.id, duration_days=30
    )
    first_expiry = user.vip_expired_at

    await service.handle_payment_succeeded(
        event_id=event_id, event_type="payment.succeeded", user_id=user.id, duration_days=30
    )

    assert user.vip_expired_at == first_expiry  # unchanged by the redelivery


@pytest.mark.asyncio
async def test_unknown_user_id_raises_for_the_caller_to_retry_or_dlq():
    service, _users, _processed = make_service()

    with pytest.raises(LookupError):
        await service.handle_payment_succeeded(
            event_id=uuid.uuid4(),
            event_type="payment.succeeded",
            user_id=uuid.uuid4(),
            duration_days=30,
        )
