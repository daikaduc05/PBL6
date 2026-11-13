"""Database queries only — see the layering note in message_repository."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from notification.models.setting import NotificationSetting


class SettingRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get(self, user_id: uuid.UUID) -> NotificationSetting | None:
        """None means "no row yet" — the caller answers with the defaults."""
        return await self._session.get(NotificationSetting, user_id)

    async def upsert(
        self,
        *,
        user_id: uuid.UUID,
        enable_daily_reminder: bool,
        reminder_hour: int,
    ) -> NotificationSetting:
        """One upsert rather than SELECT-then-INSERT: two concurrent requests
        would both see "no row" and the second INSERT would fail on the key.

        ``device_token`` is never written here, so the push token the mobile
        app stored survives every change made from the web client.
        """
        values = {
            "user_id": user_id,
            "enable_daily_reminder": enable_daily_reminder,
            "reminder_hour": reminder_hour,
        }
        stmt = (
            pg_insert(NotificationSetting)
            .values(**values)
            .on_conflict_do_update(
                index_elements=[NotificationSetting.user_id],
                set_={
                    "enable_daily_reminder": enable_daily_reminder,
                    "reminder_hour": reminder_hour,
                },
            )
            .returning(NotificationSetting)
        )
        return (await self._session.scalars(stmt)).one()

    async def user_ids_wanting_hour(self, hour: int) -> set[uuid.UUID]:
        """Users who explicitly asked to be reminded at this hour."""
        stmt = select(NotificationSetting.user_id).where(
            NotificationSetting.enable_daily_reminder.is_(True),
            NotificationSetting.reminder_hour == hour,
        )
        return set((await self._session.scalars(stmt)).all())

    async def user_ids_with_a_row(self) -> set[uuid.UUID]:
        """Everyone who has ever saved preferences.

        The scheduler needs this to tell "never configured anything" (and so
        falls back to the default hour) apart from "configured a different
        hour" — an absent row is a meaningful state here, not missing data.
        """
        stmt = select(NotificationSetting.user_id)
        return set((await self._session.scalars(stmt)).all())
