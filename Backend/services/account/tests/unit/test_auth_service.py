"""Unit tests: repository and denylist are fakes — no database, no network
(backend.md §9 testing approach)."""

from __future__ import annotations

import pytest
from account.config import AccountSettings
from account.services.auth_service import AuthService
from fakes import FakeDenylist, FakeUserRepository
from pbl6_common.errors import ConflictError, UnauthorizedError
from pbl6_common.security import hash_password


def make_settings() -> AccountSettings:
    return AccountSettings(
        database_url="postgresql+asyncpg://unused/unused",
        jwt_secret="test-secret-test-secret-test-secret",
    )


def make_service() -> tuple[AuthService, FakeUserRepository]:
    users = FakeUserRepository()
    service = AuthService(users=users, denylist=FakeDenylist(), settings=make_settings())
    return service, users


@pytest.mark.asyncio
async def test_register_creates_user_and_issues_tokens():
    service, users = make_service()
    user = await service.register(email="a@b.com", password="password123", full_name="A B")
    assert user.email == "a@b.com"
    tokens = service.issue_token_pair(user)
    assert tokens.access_token and tokens.refresh_token
    assert tokens.expires_in == 15 * 60


@pytest.mark.asyncio
async def test_register_rejects_duplicate_email():
    service, _ = make_service()
    await service.register(email="a@b.com", password="password123", full_name="A B")
    with pytest.raises(ConflictError):
        await service.register(email="A@B.com", password="password123", full_name="A B")


@pytest.mark.asyncio
async def test_authenticate_rejects_wrong_password():
    service, _ = make_service()
    await service.register(email="a@b.com", password="password123", full_name="A B")
    with pytest.raises(UnauthorizedError):
        await service.authenticate(email="a@b.com", password="wrong-password")


@pytest.mark.asyncio
async def test_authenticate_accepts_correct_password():
    service, _ = make_service()
    await service.register(email="a@b.com", password="password123", full_name="A B")
    user = await service.authenticate(email="a@b.com", password="password123")
    assert user.email == "a@b.com"


@pytest.mark.asyncio
async def test_refresh_rotates_and_revokes_old_token():
    service, _ = make_service()
    user = await service.register(email="a@b.com", password="password123", full_name="A B")
    first = service.issue_token_pair(user)

    rotated = await service.refresh(first.refresh_token)
    assert rotated.refresh_token != first.refresh_token

    # The old refresh token must now be rejected (rotation revokes it).
    with pytest.raises(UnauthorizedError):
        await service.refresh(first.refresh_token)


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token():
    service, _ = make_service()
    user = await service.register(email="a@b.com", password="password123", full_name="A B")
    tokens = service.issue_token_pair(user)

    await service.logout(tokens.refresh_token)

    with pytest.raises(UnauthorizedError):
        await service.refresh(tokens.refresh_token)


def test_password_hash_never_equals_plaintext():
    assert hash_password("password123") != "password123"
