"""Unit tests: repository is a fake — no database, no network."""

from __future__ import annotations

import uuid

import pytest
from account.services.user_service import UserService
from fakes import FakeUserRepository
from pbl6_common.errors import NotFoundError, UnauthorizedError
from pbl6_common.security import hash_password


def make_service() -> tuple[UserService, FakeUserRepository]:
    users = FakeUserRepository()
    return UserService(users=users), users


@pytest.mark.asyncio
async def test_get_profile_returns_existing_user():
    service, users = make_service()
    user = users.seed()
    fetched = await service.get_profile(user.id)
    assert fetched.id == user.id


@pytest.mark.asyncio
async def test_get_profile_raises_not_found_for_unknown_user():
    service, _ = make_service()
    with pytest.raises(NotFoundError):
        await service.get_profile(uuid.uuid4())


@pytest.mark.asyncio
async def test_update_profile_changes_full_name():
    service, users = make_service()
    user = users.seed(full_name="Old Name")
    updated = await service.update_profile(user.id, full_name="New Name")
    assert updated.full_name == "New Name"
    assert users._by_id[user.id].full_name == "New Name"


@pytest.mark.asyncio
async def test_change_password_rejects_wrong_current_password():
    service, users = make_service()
    user = users.seed(password_hash=hash_password("correct-password"))
    with pytest.raises(UnauthorizedError):
        await service.change_password(
            user.id, current_password="wrong-password", new_password="new-password123"
        )


@pytest.mark.asyncio
async def test_change_password_updates_hash_on_success():
    service, users = make_service()
    user = users.seed(password_hash=hash_password("correct-password"))
    old_hash = user.password_hash

    await service.change_password(
        user.id, current_password="correct-password", new_password="new-password123"
    )

    assert users._by_id[user.id].password_hash != old_hash
