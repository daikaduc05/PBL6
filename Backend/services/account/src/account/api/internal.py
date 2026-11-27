"""Internal API endpoints for cross-service queries (Account Service).

Allows Notification Service (and other trusted internal services) to fetch
active users or a single user's email/full_name over HTTP instead of querying
`account.users` directly across schema boundaries.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from pbl6_common.deps import verify_internal_secret
from pbl6_common.errors import NotFoundError
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from account.deps import get_db
from account.repositories.user_repository import UserRepository

router = APIRouter(
    prefix="/internal/account",
    tags=["internal"],
    dependencies=[Depends(verify_internal_secret)],
)


class InternalUserItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    role: str
    status: str


@router.get("/active-users", response_model=list[InternalUserItem])
async def list_active_users(
    session: AsyncSession = Depends(get_db),
) -> list[InternalUserItem]:
    """Returns all active, non-deleted users for study reminders and broadcasts."""
    repo = UserRepository(session)
    users = await repo.list_active_users()
    return [InternalUserItem.model_validate(u) for u in users]


@router.get("/users/{user_id}", response_model=InternalUserItem)
async def get_internal_user(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
) -> InternalUserItem:
    """Returns one non-deleted user by ID (regardless of ACTIVE/LOCKED status)
    so notification emails can reach the user."""
    repo = UserRepository(session)
    user = await repo.get_by_id(user_id)
    if user is None or user.deleted_at is not None:
        raise NotFoundError("User does not exist")
    return InternalUserItem.model_validate(user)
