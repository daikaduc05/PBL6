"""Maps 1:1 onto notification.settings.

An absent row means "all defaults" — the service never creates one on read,
so the account service does not have to seed a row at registration. That is
why DEFAULT_REMINDER_HOUR lives in Python as well as in the column default:
the scheduler has to reason about users who have no row at all.
"""

from __future__ import annotations

import uuid

from pbl6_common.db import Base
from sqlalchemy import Boolean, CheckConstraint, Index, SmallInteger, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

# Hour of day (0-23, Asia/Ho_Chi_Minh) a learner is reminded when they have
# never chosen one.
DEFAULT_REMINDER_HOUR = 20


class NotificationSetting(Base):
    __tablename__ = "settings"
    __table_args__ = (
        CheckConstraint(
            "reminder_hour >= 0 AND reminder_hour <= 23",
            name="settings_reminder_hour_check",
        ),
        Index(
            "settings_reminder_hour_idx",
            "reminder_hour",
            postgresql_where=text("enable_daily_reminder = true"),
        ),
        {"schema": "notification"},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    enable_daily_reminder: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    # Local hour the learner wants to be nudged at. Hour precision only: the
    # scheduler wakes once an hour, so minutes would be stored and ignored.
    reminder_hour: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("20")
    )
    # Expo push token, written by the mobile app only. The web settings
    # endpoint deliberately cannot touch it.
    device_token: Mapped[str | None] = mapped_column(Text, nullable=True)
