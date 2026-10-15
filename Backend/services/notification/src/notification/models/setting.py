"""Maps 1:1 onto notification.settings (Backend/db/05_notification.sql).

An absent row means "all defaults" — the service never creates one on read,
so the account service does not have to seed a row at registration.
"""

from __future__ import annotations

import uuid

from pbl6_common.db import Base
from sqlalchemy import Boolean, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class NotificationSetting(Base):
    __tablename__ = "settings"
    __table_args__ = {"schema": "notification"}

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    enable_daily_reminder: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    # Expo push token, written by the mobile app only. The web settings
    # endpoint deliberately cannot touch it.
    device_token: Mapped[str | None] = mapped_column(Text, nullable=True)
