"""Database queries only — never raises an HTTP exception (backend.md §3
layering rule: api -> services -> repositories -> models)."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Any, cast

from sqlalchemy import ColumnElement, CursorResult, and_, delete, func, select, true, update
from sqlalchemy.ext.asyncio import AsyncSession

from notification.models.message import Message, MessageType


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

    async def create(
        self, *, user_id: uuid.UUID, title: str, content: str, type: MessageType
    ) -> Message:
        message = Message(user_id=user_id, title=title, content=content, type=type)
        self._session.add(message)
        await self._session.flush()  # populate server defaults; the request commits
        return message

    async def user_ids_with_type_since(
        self, *, type: MessageType, since: datetime
    ) -> set[uuid.UUID]:
        """Who already received a notification of this kind today.

        How the reminder job avoids sending twice when it is re-run, or when
        the service restarts right as the hour ticks over. Keyed on the type
        column rather than the title: reworded display copy used to make this
        query match nothing, which reminded everyone once an hour and raised
        no error doing it.
        """
        stmt = (
            select(Message.user_id)
            .where(Message.type == type, Message.created_at >= since)
            .distinct()
        )
        return set((await self._session.scalars(stmt)).all())

    def _filter(self, *, unread_only: bool, type: MessageType | None) -> ColumnElement[bool]:
        """The caller's filter, minus the owner check every query applies anyway.

        ``true()`` seeds it so "no filter at all" is an ordinary case rather
        than a branch, and so the same expression can be dropped into both the
        listing's WHERE and the counting query's FILTER clause — which is what
        keeps the row count and the rows themselves from ever disagreeing.
        """
        conditions: list[ColumnElement[bool]] = []
        if unread_only:
            conditions.append(Message.is_read.is_(False))
        if type is not None:
            conditions.append(Message.type == type)
        return and_(true(), *conditions)

    async def count(
        self, *, user_id: uuid.UUID, unread_only: bool = False, type: MessageType | None = None
    ) -> tuple[int, int]:
        """Return (rows matching the filter, unread total ignoring it).

        Both in one round-trip. The second figure is what the bell badge shows,
        so it must stay whole even while the user is looking at a filtered list.
        """
        row = await self._session.execute(
            select(
                func.count().filter(self._filter(unread_only=unread_only, type=type)),
                func.count().filter(Message.is_read.is_(False)),
            )
            .select_from(Message)
            .where(Message.user_id == user_id)
        )
        matching, unread = row.one()
        return matching, unread

    async def list_for_user(
        self,
        *,
        user_id: uuid.UUID,
        page: int,
        size: int,
        unread_only: bool,
        type: MessageType | None = None,
    ) -> Sequence[Message]:
        stmt = select(Message).where(
            Message.user_id == user_id, self._filter(unread_only=unread_only, type=type)
        )

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
