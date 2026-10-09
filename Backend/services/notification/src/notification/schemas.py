"""Request and response shapes for the notification API (functions 8.3-8.5)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MessageOut(BaseModel):
    """One in-app notification as the client sees it."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    content: str
    is_read: bool
    created_at: datetime


class MessagePage(BaseModel):
    """A page of notifications (function 8.3)."""

    items: list[MessageOut]
    total: int = Field(description="Total rows matching the current filter")
    page: int
    size: int
    unread_count: int = Field(
        description="Unread total, ignoring the filter — the web badge needs this "
        "even while the user is viewing read messages"
    )


class BulkUpdateOut(BaseModel):
    updated: int


class SettingsOut(BaseModel):
    """Current preferences. An absent row reads back as the defaults."""

    model_config = ConfigDict(from_attributes=True)

    enable_daily_reminder: bool
    device_token: str | None = None


class SettingsIn(BaseModel):
    """Function 8.5 — the on/off switch.

    ``device_token`` is intentionally **not** accepted here. It is written by
    the mobile app, and letting the web client PUT the whole settings object
    would wipe the push token every time someone toggled the reminder.
    """

    enable_daily_reminder: bool
