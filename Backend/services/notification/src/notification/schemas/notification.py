"""Request and response shapes for functions 8.3, 8.4 and 8.5."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from notification.models.setting import DEFAULT_REMINDER_HOUR


class MessageResponse(BaseModel):
    """One in-app notification as the client sees it."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    content: str
    is_read: bool
    created_at: datetime


class MessagePage(BaseModel):
    """Function 8.3. Extends the shared pagination envelope with unread_count.

    ``pbl6_common.pagination.Paginated`` carries items/total/page/size; the web
    badge also needs the unread figure while the user is reading, so this page
    adds that one field rather than making every service carry it.
    """

    items: list[MessageResponse]
    total: int = Field(description="Rows matching the current filter")
    page: int
    size: int
    unread_count: int = Field(description="Unread total, ignoring the filter")


class BulkUpdateResponse(BaseModel):
    updated: int


class SettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    enable_daily_reminder: bool
    reminder_hour: int = Field(description="Local hour (0-23, Asia/Ho_Chi_Minh)")
    device_token: str | None = None


class UpdateSettingsRequest(BaseModel):
    """Function 8.5 — reminder preferences.

    ``device_token`` is intentionally not accepted: it is written by the mobile
    app, and letting the web client send the whole settings object would wipe
    the push token every time someone changed their reminder time.
    """

    enable_daily_reminder: bool
    # An early riser picks 7, a night owl picks 22. Hour precision only — the
    # scheduler wakes once an hour, so minutes would be stored and ignored.
    reminder_hour: int = Field(
        default=DEFAULT_REMINDER_HOUR,
        ge=0,
        le=23,
        description="Local hour to be reminded at (0-23, Asia/Ho_Chi_Minh)",
    )
