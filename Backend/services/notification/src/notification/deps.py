"""Service-local dependency wiring: this service's own engine, session and
service factories. `pbl6_common.deps` covers the auth dependencies shared
across services (get_current_user, require_role, require_vip)."""

from __future__ import annotations

from fastapi import Depends
from pbl6_common.db import make_engine, make_get_db, make_session_factory
from sqlalchemy.ext.asyncio import AsyncSession

from notification.config import get_settings
from notification.repositories.message_repository import MessageRepository
from notification.repositories.setting_repository import SettingRepository
from notification.services.notification_service import NotificationService

settings = get_settings()
engine = make_engine(settings.database_url)
_session_factory = make_session_factory(engine)

# Commits once per successful request and rolls back on error, so no service
# or repository below ever calls commit() itself.
get_db = make_get_db(_session_factory)


def get_notification_service(
    session: AsyncSession = Depends(get_db),
) -> NotificationService:
    return NotificationService(
        messages=MessageRepository(session),
        settings=SettingRepository(session),
    )
