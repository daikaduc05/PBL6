"""Database queries only — never raises an HTTP exception (backend.md §3
layering rule: api -> services -> repositories -> models)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from account.models.password_reset_token import PasswordResetToken


class PasswordResetRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self, *, user_id: uuid.UUID, token_hash: str, expires_at: datetime
    ) -> PasswordResetToken:
        entry = PasswordResetToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def get_valid(self, token_hash: str) -> PasswordResetToken | None:
        """Only returns a row that hasn't expired and hasn't already been
        redeemed — an invalid/expired/used token is indistinguishable from
        the caller's perspective, same as a 401 doesn't say which."""
        now = datetime.now(UTC)
        stmt = select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.expires_at > now,
            PasswordResetToken.used_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_used(self, entry: PasswordResetToken) -> None:
        entry.used_at = datetime.now(UTC)
        await self._session.flush()
