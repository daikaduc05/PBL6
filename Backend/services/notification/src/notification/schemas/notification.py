"""Request and response shapes for functions 8.3, 8.4 and 8.5."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


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
    device_token: str | None = None


class UpdateSettingsRequest(BaseModel):
    """Function 8.5 — the on/off switch.

    ``device_token`` is intentionally not accepted: it is written by the mobile
    app, and letting the web client send the whole settings object would wipe
    the push token every time someone toggled the reminder.
    """

    enable_daily_reminder: bool
