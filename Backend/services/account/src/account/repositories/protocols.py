"""Structural (Protocol) types for account's repositories — service
constructors type-hint against these, not the concrete classes, so a unit
test's fake repository satisfies the check by shape instead of needing to
inherit from it (same pattern as payment.repositories.protocols)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Protocol

from account.models.password_reset_token import PasswordResetToken
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


class ProcessedEventRepositoryProtocol(Protocol):
    async def already_processed(self, event_id: uuid.UUID) -> bool: ...

    async def mark_processed(self, *, event_id: uuid.UUID, event_type: str) -> None: ...


class PasswordResetRepositoryProtocol(Protocol):
    async def create(
        self, *, user_id: uuid.UUID, token_hash: str, expires_at: datetime
    ) -> PasswordResetToken: ...

    async def get_valid(self, token_hash: str) -> PasswordResetToken | None: ...

    async def mark_used(self, entry: PasswordResetToken) -> None: ...
