"""T13 — HTTP layer only, no business logic (backend.md §3 layering rule).

    GET    /api/v1/notifications                 8.3  view
    PATCH  /api/v1/notifications/read-all        8.3  mark everything read
    PATCH  /api/v1/notifications/{id}/read       8.3  mark one read
    DELETE /api/v1/notifications/{id}            8.4  delete
    GET    /api/v1/notifications/settings        8.5  read preferences
    PUT    /api/v1/notifications/settings        8.5  turn reminders on/off

"authenticated" means the gateway verified the JWT and forwarded X-User-Id
(backend.md §7). There is no gateway yet (T08/T09), so set the header by hand
when calling these directly.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from pbl6_common.deps import UserContext, get_current_user

from notification.deps import get_notification_service
from notification.schemas.notification import (
    BulkUpdateResponse,
    MessagePage,
    MessageResponse,
    SettingsResponse,
    UpdateSettingsRequest,
)
from notification.services.notification_service import (
    DEFAULT_ENABLE_DAILY_REMINDER,
    NotificationService,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])

# Literal paths come before "/{message_id}" ones: FastAPI matches in
# declaration order, so a future GET /{message_id} must not shadow /settings.


@router.get("/settings", response_model=SettingsResponse, summary="8.5 — Read preferences")
async def read_settings(
    user: UserContext = Depends(get_current_user),
    svc: NotificationService = Depends(get_notification_service),
):
    row = await svc.get_settings(uuid.UUID(user.user_id))
    if row is None:
        return SettingsResponse(
            enable_daily_reminder=DEFAULT_ENABLE_DAILY_REMINDER, device_token=None
        )
    return row


@router.put("/settings", response_model=SettingsResponse, summary="8.5 — Toggle reminders")
async def update_settings(
    body: UpdateSettingsRequest,
    user: UserContext = Depends(get_current_user),
    svc: NotificationService = Depends(get_notification_service),
):
    return await svc.update_settings(
        user_id=uuid.UUID(user.user_id), enable_daily_reminder=body.enable_daily_reminder
    )


@router.patch("/read-all", response_model=BulkUpdateResponse, summary="8.3 — Mark all read")
async def mark_all_read(
    user: UserContext = Depends(get_current_user),
    svc: NotificationService = Depends(get_notification_service),
):
    updated = await svc.mark_all_read(uuid.UUID(user.user_id))
    return BulkUpdateResponse(updated=updated)


@router.get("", response_model=MessagePage, summary="8.3 — List notifications")
async def list_notifications(
    user: UserContext = Depends(get_current_user),
    svc: NotificationService = Depends(get_notification_service),
    page: Annotated[int, Query(ge=1)] = 1,
    # Capped so a client cannot pull the whole table in one request.
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    unread_only: bool = False,
):
    items, total, unread_count = await svc.list_for_user(
        user_id=uuid.UUID(user.user_id), page=page, size=size, unread_only=unread_only
    )
    return MessagePage(
        items=[MessageResponse.model_validate(m) for m in items],
        total=total,
        page=page,
        size=size,
        unread_count=unread_count,
    )


@router.patch(
    "/{message_id}/read",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="8.3 — Mark one read",
)
async def mark_read(
    message_id: uuid.UUID,
    user: UserContext = Depends(get_current_user),
    svc: NotificationService = Depends(get_notification_service),
):
    await svc.mark_read(user_id=uuid.UUID(user.user_id), message_id=message_id)


@router.delete(
    "/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="8.4 — Delete a notification",
)
async def delete_notification(
    message_id: uuid.UUID,
    user: UserContext = Depends(get_current_user),
    svc: NotificationService = Depends(get_notification_service),
):
    await svc.delete(user_id=uuid.UUID(user.user_id), message_id=message_id)
