"""Unit tests: repository and denylist are fakes — no database, no network
(backend.md §9 testing approach)."""

from __future__ import annotations

import uuid

import pytest
from account.config import AccountSettings
from account.models.user import User
from account.services.auth_service import AuthService
from pbl6_common.errors import ConflictError, UnauthorizedError
from pbl6_common.security import hash_password


class FakeUserRepository:
    def __init__(self):
        self._by_id: dict[uuid.UUID, User] = {}

    async def get_by_email(self, email: str) -> User | None:
        return next((u for u in self._by_id.values() if u.email.lower() == email.lower()), None)

    async def get_by_id(self, user_id) -> User | None:
        return self._by_id.get(uuid.UUID(str(user_id)))

    async def create(self, *, email: str, password_hash: str, full_name: str) -> User:
        user = User(
            id=uuid.uuid4(),
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            role="CUSTOMER",
            status="ACTIVE",
            is_vip=False,
        )
        self._by_id[user.id] = user
        return user


class FakeDenylist:
    def __init__(self):
        self._revoked: set[str] = set()

    async def revoke(self, jti: str, *, ttl_seconds: int) -> None:
        self._revoked.add(jti)

    async def is_revoked(self, jti: str) -> bool:
        return jti in self._revoked


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
