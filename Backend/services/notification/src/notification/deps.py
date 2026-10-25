"""Service-local dependency wiring: this service's own engine, session and
service factories. `pbl6_common.deps` covers the auth dependencies shared
across services (get_current_user, require_role, require_vip)."""

from __future__ import annotations

from fastapi import Depends
from pbl6_common.db import make_engine, make_get_db, make_session_factory
from sqlalchemy.ext.asyncio import AsyncSession

from notification.config import get_settings
from notification.email.sender import make_sender
from notification.repositories.message_repository import MessageRepository
from notification.repositories.setting_repository import SettingRepository
from notification.services.email_service import EmailService
from notification.services.notification_service import NotificationService

settings = get_settings()
engine = make_engine(settings.database_url)
_session_factory = make_session_factory(engine)

# Commits once per successful request and rolls back on error, so no service
# or repository below ever calls commit() itself.
get_db = make_get_db(_session_factory)

# Stateless and holds no connection — one instance for the process. The 20:00
# cron (T14) and the event consumer (T16) use it directly rather than through
# Depends, since neither runs inside a request.
email_service = EmailService(make_sender(settings), app_url=settings.app_url)


def get_notification_service(
    session: AsyncSession = Depends(get_db),
) -> NotificationService:
    return NotificationService(
        messages=MessageRepository(session),
        settings=SettingRepository(session),
    )


def get_email_service() -> EmailService:
    return email_service
