"""Unit tests: repository/publisher are fakes — no database, no network."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from account.models.user import User
from account.services.vip_expiry_service import VipExpiryService


class FakeUserRepository:
    def __init__(self) -> None:
        self._by_id: dict[uuid.UUID, User] = {}

    async def save(self, user: User) -> None:
        self._by_id[user.id] = user

    async def list_expired_vip(self, *, now: datetime, limit: int = 500) -> list[User]:
        return [
            u
            for u in self._by_id.values()
            if u.is_vip and u.vip_expired_at is not None and u.vip_expired_at < now
        ][:limit]

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


class FakeEventPublisher:
    def __init__(self) -> None:
        self.published: list[tuple[str, dict]] = []

    async def publish(self, event_type: str, data: dict) -> None:
        self.published.append((event_type, data))


def make_service() -> tuple[VipExpiryService, FakeUserRepository, FakeEventPublisher]:
    users = FakeUserRepository()
    publisher = FakeEventPublisher()
    return VipExpiryService(users=users, publisher=publisher), users, publisher


@pytest.mark.asyncio
async def test_sweep_revokes_vip_and_clears_expiry():
    service, users, _publisher = make_service()
    lapsed = datetime.now(UTC) - timedelta(days=1)
    user = users.seed(is_vip=True, vip_expired_at=lapsed)

    revoked = await service.sweep()

    assert revoked == 1
    assert user.is_vip is False
    assert user.vip_expired_at is None


@pytest.mark.asyncio
async def test_sweep_publishes_vip_expired_with_the_original_expiry():
    service, users, publisher = make_service()
    lapsed = datetime.now(UTC) - timedelta(days=1)
    user = users.seed(is_vip=True, vip_expired_at=lapsed)

    await service.sweep()

    assert publisher.published == [
        ("vip.expired", {"user_id": str(user.id), "expired_at": lapsed.isoformat()})
    ]


@pytest.mark.asyncio
async def test_sweep_leaves_still_valid_vip_users_untouched():
    service, users, publisher = make_service()
    still_valid = users.seed(is_vip=True, vip_expired_at=datetime.now(UTC) + timedelta(days=5))

    revoked = await service.sweep()

    assert revoked == 0
    assert still_valid.is_vip is True
    assert publisher.published == []


@pytest.mark.asyncio
async def test_sweep_leaves_non_vip_users_untouched():
    service, users, publisher = make_service()
    users.seed(is_vip=False, vip_expired_at=None)

    revoked = await service.sweep()

    assert revoked == 0
    assert publisher.published == []


@pytest.mark.asyncio
async def test_sweep_handles_multiple_expired_users_in_one_run():
    service, users, publisher = make_service()
    lapsed = datetime.now(UTC) - timedelta(days=1)
    users.seed(is_vip=True, vip_expired_at=lapsed)
    users.seed(is_vip=True, vip_expired_at=lapsed)

    revoked = await service.sweep()

    assert revoked == 2
    assert len(publisher.published) == 2
