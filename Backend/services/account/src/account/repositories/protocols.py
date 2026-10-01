"""Structural (Protocol) type for UserRepository — service constructors
type-hint against this, not the concrete class, so a unit test's fake
repository satisfies the check by shape instead of needing to inherit from
it (same reasoning as pbl6_common.security.RefreshTokenDenylistProtocol)."""

from __future__ import annotations

import uuid
from typing import Protocol

from account.models.user import User


class UserRepositoryProtocol(Protocol):
    async def get_by_email(self, email: str) -> User | None: ...
    async def get_by_id(self, user_id: uuid.UUID) -> User | None: ...

    async def create(
        self, *, email: str, password_hash: str, full_name: str, role: str = "CUSTOMER"
    ) -> User: ...

    async def save(self, user: User) -> None: ...

    async def list_by_role(
        self,
        *,
        role: str,
        page: int,
        size: int,
        status: str | None = None,
        q: str | None = None,
    ) -> tuple[list[User], int]: ...
