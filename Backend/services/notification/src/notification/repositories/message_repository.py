"""Database queries only — never raises an HTTP exception (backend.md §3
layering rule: api -> services -> repositories -> models)."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Any, cast

from sqlalchemy import CursorResult, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from notification.models.message import Message


def _affected_rows(result: Any) -> int:
    """Row count of an UPDATE/DELETE.

    ``Session.execute`` is typed as returning ``Result``, which has no
    ``rowcount``; DML actually yields a ``CursorResult``. The cast tells mypy
    what SQLAlchemy guarantees at runtime for these statements.
    """
    return cast("CursorResult[Any]", result).rowcount


class MessageRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, *, user_id: uuid.UUID, title: str, content: str) -> Message:
        message = Message(user_id=user_id, title=title, content=content)
        self._session.add(message)
        await self._session.flush()  # populate server defaults; the request commits
        return message

    async def count(self, user_id: uuid.UUID) -> tuple[int, int]:
        """Return (total, unread) in one round-trip."""
        row = await self._session.execute(
            select(func.count(), func.count().filter(Message.is_read.is_(False)))
            .select_from(Message)
            .where(Message.user_id == user_id)
        )
        total, unread = row.one()
        return total, unread

    async def list_for_user(
        self, *, user_id: uuid.UUID, page: int, size: int, unread_only: bool
    ) -> Sequence[Message]:
        stmt = select(Message).where(Message.user_id == user_id)
        if unread_only:
            stmt = stmt.where(Message.is_read.is_(False))

        # id is a tie-breaker, not decoration: the daily cron inserts a batch
        # of rows within the same millisecond, and ordering by created_at alone
        # would let one row show up on two different pages.
        stmt = (
            stmt.order_by(Message.created_at.desc(), Message.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        return (await self._session.scalars(stmt)).all()

    async def mark_read(self, *, user_id: uuid.UUID, message_id: uuid.UUID) -> bool:
        """False when the row is not this user's. Idempotent otherwise."""
        result = await self._session.execute(
            update(Message)
            .where(Message.id == message_id, Message.user_id == user_id)
            .values(is_read=True)
        )
        return _affected_rows(result) > 0

    async def mark_all_read(self, user_id: uuid.UUID) -> int:
        result = await self._session.execute(
            update(Message)
            .where(Message.user_id == user_id, Message.is_read.is_(False))
            .values(is_read=True)
        )
        return _affected_rows(result)

    async def delete(self, *, user_id: uuid.UUID, message_id: uuid.UUID) -> bool:
        """Hard delete — the table has no deleted_at, and a notification the
        user chose to remove is not audit data.

        ``user_id`` stays in the WHERE clause even though the service already
        knows the caller, so a bug in a layer above still cannot reach another
        user's row.
        """
        result = await self._session.execute(
            delete(Message).where(Message.id == message_id, Message.user_id == user_id)
        )
        return _affected_rows(result) > 0
