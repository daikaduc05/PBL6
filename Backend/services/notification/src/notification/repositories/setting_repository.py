"""Database queries only — see the layering note in message_repository."""

from __future__ import annotations

import uuid

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
        self, *, user_id: uuid.UUID, enable_daily_reminder: bool
    ) -> NotificationSetting:
        """One upsert rather than SELECT-then-INSERT: two concurrent requests
        would both see "no row" and the second INSERT would fail on the key.

        Only ``enable_daily_reminder`` is written, so ``device_token`` set by
        the mobile app survives every toggle from the web client.
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
        return (await self._session.scalars(stmt)).one()
