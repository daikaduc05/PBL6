"""HTTP endpoints for functions 8.3 (view), 8.4 (delete) and 8.5 (toggle)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from notification.db import get_session
from notification.deps import CurrentUserDep
from notification.errors import NotFoundError
from notification.notifications import service
from notification.schemas import (
    BulkUpdateOut,
    MessageOut,
    MessagePage,
    SettingsIn,
    SettingsOut,
)

SessionDep = Annotated[AsyncSession, Depends(get_session)]

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])

# Literal paths are declared before "/{message_id}" ones. FastAPI matches in
# declaration order, so a future GET /{message_id} must not shadow /settings.


@router.get(
    "/settings",
    response_model=SettingsOut,
    summary="8.5 — Read notification preferences",
)
async def read_settings(user: CurrentUserDep, session: SessionDep) -> SettingsOut:
    """Return the user's preferences, or the defaults if they never set any."""
    row = await service.get_settings(session, user.id)
    if row is None:
        return SettingsOut(enable_daily_reminder=True, device_token=None)
    return SettingsOut.model_validate(row)


@router.put(
    "/settings",
    response_model=SettingsOut,
    summary="8.5 — Turn daily reminders on or off",
)
async def write_settings(
    payload: SettingsIn, user: CurrentUserDep, session: SessionDep
) -> SettingsOut:
    """Switch the daily study reminder on or off.

    Scope of the switch: it silences the **daily reminder** on both channels
    (in-app and email). Transactional notifications — payment succeeded, VIP
    expired, account locked — are always delivered, because a user who does not
    learn their account was locked or their card was charged is worse off than
    one who receives an unwanted message.
    """
    row = await service.upsert_settings(session, user.id, payload.enable_daily_reminder)
    await session.commit()
    return SettingsOut.model_validate(row)


@router.patch(
    "/read-all",
    response_model=BulkUpdateOut,
    summary="8.3 — Mark every notification read",
)
async def mark_all_read(user: CurrentUserDep, session: SessionDep) -> BulkUpdateOut:
    updated = await service.mark_all_read(session, user.id)
    await session.commit()
    return BulkUpdateOut(updated=updated)


@router.get("", response_model=MessagePage, summary="8.3 — List notifications")
async def list_notifications(
    user: CurrentUserDep,
    session: SessionDep,
    page: Annotated[int, Query(ge=1)] = 1,
    # Capped so a client cannot ask for the entire table in one request.
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    unread_only: bool = False,
) -> MessagePage:
    """Newest first. `unread_only=true` uses the partial index on unread rows."""
    items, total, unread_count = await service.list_messages(
        session, user.id, page=page, size=size, unread_only=unread_only
    )
    return MessagePage(
        items=[MessageOut.model_validate(m) for m in items],
        total=total,
        page=page,
        size=size,
        unread_count=unread_count,
    )


@router.patch(
    "/{message_id}/read",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="8.3 — Mark one notification read",
)
async def mark_read(message_id: uuid.UUID, user: CurrentUserDep, session: SessionDep) -> Response:
    if not await service.mark_read(session, user.id, message_id):
        raise NotFoundError("Notification does not exist")
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="8.4 — Delete a notification",
)
async def delete_notification(
    message_id: uuid.UUID, user: CurrentUserDep, session: SessionDep
) -> Response:
    """Delete one of the caller's own notifications.

    Returns 404 — not 403 — when the id belongs to someone else. A 403 would
    confirm that the id exists and is another user's, which is more than an
    attacker should learn.
    """
    if not await service.delete_message(session, user.id, message_id):
        raise NotFoundError("Notification does not exist")
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
