"""Business rules for in-app notifications and user preferences.

Layering (backend.md §3): the API layer calls this, this calls repositories.
HTTP concerns stop here — the API never touches a repository and this module
never builds a response model.

Transactions: ``pbl6_common.db.make_get_db`` commits once per successful
request, so nothing here commits. That matters for T16: the consumer needs to
write a message and its processed_events row inside one transaction, which
would be impossible if this layer committed on its own.
"""

from __future__ import annotations

import uuid

from pbl6_common.errors import NotFoundError

from notification.models.message import Message
from notification.models.setting import NotificationSetting
from notification.repositories.message_repository import MessageRepository
from notification.repositories.setting_repository import SettingRepository

# Every notification the daily reminder produces carries this exact title; the
# cron job (T14) uses it to detect "already reminded today".
STUDY_REMINDER_TITLE = "It's time to study"

# Returned when no preferences row exists. Reading must not create one.
DEFAULT_ENABLE_DAILY_REMINDER = True


class NotificationService:
    def __init__(self, *, messages: MessageRepository, settings: SettingRepository):
        self._messages = messages
        self._settings = settings

    # --- function 8.2: creating notifications -----------------------------

    async def create(self, *, user_id: uuid.UUID, title: str, content: str) -> Message:
        """The single entry point for all three producers — API, the 20:00 cron
        job and the RabbitMQ consumer — so a later change (audit trail, push
        fan-out) lands in exactly one place."""
        return await self._messages.create(user_id=user_id, title=title, content=content)

    # --- function 8.3: viewing --------------------------------------------

    async def list_for_user(
        self, *, user_id: uuid.UUID, page: int, size: int, unread_only: bool
    ) -> tuple[list[Message], int, int]:
        """Return (items, total, unread_count)."""
        total_all, unread_count = await self._messages.count(user_id)
        items = await self._messages.list_for_user(
            user_id=user_id, page=page, size=size, unread_only=unread_only
        )
        total = unread_count if unread_only else total_all
        return list(items), total, unread_count

    async def mark_read(self, *, user_id: uuid.UUID, message_id: uuid.UUID) -> None:
        if not await self._messages.mark_read(user_id=user_id, message_id=message_id):
            raise NotFoundError("notification does not exist")

    async def mark_all_read(self, user_id: uuid.UUID) -> int:
        return await self._messages.mark_all_read(user_id)

    # --- function 8.4: deleting -------------------------------------------

    async def delete(self, *, user_id: uuid.UUID, message_id: uuid.UUID) -> None:
        """Raises NotFoundError — not ForbiddenError — for someone else's row.

        A 403 would confirm the id exists and belongs to another user, which is
        more than a caller should be able to learn.
        """
        if not await self._messages.delete(user_id=user_id, message_id=message_id):
            raise NotFoundError("notification does not exist")

    # --- function 8.5: preferences ----------------------------------------

    async def get_settings(self, user_id: uuid.UUID) -> NotificationSetting | None:
        """None means the user never set anything; the API answers defaults."""
        return await self._settings.get(user_id)

    async def update_settings(
        self, *, user_id: uuid.UUID, enable_daily_reminder: bool
    ) -> NotificationSetting:
        """Switch the daily reminder on or off.

        Scope: this silences the **daily study reminder** on both channels.
        Transactional notifications — payment succeeded, VIP expired, account
        locked — are always delivered, because a user who never learns their
        account was locked or their card was charged is worse off than one who
        receives a message they did not want.
        """
        return await self._settings.upsert(
            user_id=user_id, enable_daily_reminder=enable_daily_reminder
        )
