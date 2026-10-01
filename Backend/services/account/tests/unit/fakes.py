"""Shared test doubles for account service unit tests.

One canonical FakeUserRepository/FakeDenylist implementing the FULL
Protocol each service constructor expects (account.repositories.protocols.
UserRepositoryProtocol / pbl6_common.security.RefreshTokenDenylistProtocol).
Previously every test file hand-rolled its own partial Fake — each one
missing different methods — which is exactly what broke mypy the moment
Protocol typing was introduced (T28). One shared, complete fake can't drift
out of sync like that.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from account.models.user import User


class FakeUserRepository:
    def __init__(self) -> None:
        self._by_id: dict[uuid.UUID, User] = {}

    async def get_by_email(self, email: str) -> User | None:
        return next((u for u in self._by_id.values() if u.email.lower() == email.lower()), None)

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        # AuthService.refresh passes the JWT's raw `sub` string, not a UUID
        # instance — the real repository tolerates that via SQLAlchemy's
        # type coercion (verified against Supabase), so normalize here too.
        key = user_id if isinstance(user_id, uuid.UUID) else uuid.UUID(str(user_id))
        return self._by_id.get(key)

    async def create(
        self, *, email: str, password_hash: str, full_name: str, role: str = "CUSTOMER"
    ) -> User:
        user = User(
            id=uuid.uuid4(),
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            role=role,
            status="ACTIVE",
            is_vip=False,
            created_at=datetime.now(UTC),
        )
        self._by_id[user.id] = user
        return user

    async def save(self, user: User) -> None:
        self._by_id[user.id] = user

    async def list_by_role(
        self,
        *,
        role: str,
        page: int,
        size: int,
        status: str | None = None,
        q: str | None = None,
    ) -> tuple[list[User], int]:
        matches = [u for u in self._by_id.values() if u.role == role and not u.deleted_at]
        if status is not None:
            matches = [u for u in matches if u.status == status]
        if q:
            needle = q.lower()
            matches = [
                u for u in matches if needle in u.full_name.lower() or needle in u.email.lower()
            ]
        matches.sort(key=lambda u: u.created_at, reverse=True)
        start = (page - 1) * size
        return matches[start : start + size], len(matches)

    def seed(self, **kwargs) -> User:
        user = User(
            id=uuid.uuid4(),
            email=kwargs.pop("email", f"{uuid.uuid4()}@vidu.com"),
            password_hash=kwargs.pop("password_hash", "x"),
            full_name=kwargs.pop("full_name", "A B"),
            role=kwargs.pop("role", "CUSTOMER"),
            status=kwargs.pop("status", "ACTIVE"),
            is_vip=kwargs.pop("is_vip", False),
            created_at=kwargs.pop("created_at", datetime.now(UTC)),
        )
        self._by_id[user.id] = user
        return user


class FakeDenylist:
    def __init__(self) -> None:
        self._revoked: set[str] = set()

    async def revoke(self, jti: str, *, ttl_seconds: int) -> None:
        self._revoked.add(jti)

    async def is_revoked(self, jti: str) -> bool:
        return jti in self._revoked
