"""Business logic for in-app notifications and user preferences.

Transaction policy: **nothing here commits.** The caller owns the transaction
boundary, because the RabbitMQ consumer (T16) must write a message and its
``processed_events`` row in one atomic unit — if this module committed on its
own, that guarantee would be impossible.
"""

import uuid
from collections.abc import Sequence

from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from notification.models import Message, NotificationSetting

# Every notification the daily reminder produces carries this exact title; the
# cron job (T14) uses it to detect "already reminded today".
STUDY_REMINDER_TITLE = "It's time to study"


async def create_message(
    session: AsyncSession, user_id: uuid.UUID, title: str, content: str
) -> Message:
    """Create one in-app notification (function 8.2).

    The single entry point for all three producers — API, cron job and event
    consumer — so a future change (audit log, push fan-out) lands in one place.
    """
    message = Message(user_id=user_id, title=title, content=content)
    session.add(message)
    await session.flush()  # populate server defaults without committing
    return message


async def list_messages(
    session: AsyncSession,
    user_id: uuid.UUID,
    page: int,
    size: int,
    unread_only: bool,
) -> tuple[Sequence[Message], int, int]:
    """Return (items, total, unread_count) for function 8.3."""
    # Both counts in one round-trip: the unread figure is needed for the badge
    # regardless of the filter the user is currently viewing.
    total_all, unread_count = (
        await session.execute(
            select(
                func.count(),
                func.count().filter(Message.is_read.is_(False)),
            )
            .select_from(Message)
            .where(Message.user_id == user_id)
        )
    ).one()

    stmt = select(Message).where(Message.user_id == user_id)
    if unread_only:
        stmt = stmt.where(Message.is_read.is_(False))

    # id is a tie-breaker, not decoration: the cron job inserts a batch of rows
    # within the same millisecond, and ordering by created_at alone would let
    # the same row appear on two pages.
    items = (
        await session.scalars(
            stmt.order_by(Message.created_at.desc(), Message.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
    ).all()

    return items, (unread_count if unread_only else total_all), unread_count


async def mark_read(session: AsyncSession, user_id: uuid.UUID, message_id: uuid.UUID) -> bool:
    """Mark one notification read. False when it does not belong to the user.

    Idempotent — marking an already-read message succeeds.
    """
    result = await session.execute(
        update(Message)
        .where(Message.id == message_id, Message.user_id == user_id)
        .values(is_read=True)
    )
    return result.rowcount > 0


async def mark_all_read(session: AsyncSession, user_id: uuid.UUID) -> int:
    result = await session.execute(
        update(Message)
        .where(Message.user_id == user_id, Message.is_read.is_(False))
        .values(is_read=True)
    )
    return result.rowcount


async def delete_message(session: AsyncSession, user_id: uuid.UUID, message_id: uuid.UUID) -> bool:
    """Delete one notification (function 8.4). False when not the user's own.

    A hard delete: ``notification.messages`` has no ``deleted_at`` column, and
    a notification the user chose to remove is not audit data.

    ``user_id`` stays in the WHERE clause even though the caller already
    checked identity — so a bug in the layer above still cannot delete another
    user's row.
    """
    result = await session.execute(
        delete(Message).where(Message.id == message_id, Message.user_id == user_id)
    )
    return result.rowcount > 0


async def get_settings(session: AsyncSession, user_id: uuid.UUID) -> NotificationSetting | None:
    """Read preferences. None means "no row yet" — the caller returns defaults.

    Deliberately does not create the row: the account service would otherwise
    have to seed one at registration, and the table stays limited to users who
    actually changed something.
    """
    return await session.get(NotificationSetting, user_id)


async def upsert_settings(
    session: AsyncSession, user_id: uuid.UUID, enable_daily_reminder: bool
) -> NotificationSetting:
    """Create or update preferences (function 8.5).

    One upsert rather than SELECT-then-INSERT: two concurrent requests would
    both see "no row" and the second INSERT would fail on the primary key.
    """
    stmt = (
        pg_insert(NotificationSetting)
        .values(user_id=user_id, enable_daily_reminder=enable_daily_reminder)
        .on_conflict_do_update(
            index_elements=[NotificationSetting.user_id],
            set_={"enable_daily_reminder": enable_daily_reminder},
        )
        .returning(NotificationSetting)
    )
    return (await session.scalars(stmt)).one()
