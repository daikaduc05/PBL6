"""T23 business logic — admin management of student (role=CUSTOMER) accounts.

Editor accounts have a separate screen (T24) with their own service; this
one deliberately only ever touches role=CUSTOMER rows so it can't be used
as a side door to lock/promote an editor or admin account.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from account.models.user import User
from account.repositories.user_repository import UserRepository
from pbl6_common.errors import NotFoundError


class AdminUserService:
    def __init__(self, users: UserRepository):
        self._users = users

    async def list_students(self, *, page: int, size: int) -> tuple[list[User], int]:
        return await self._users.list_customers(page=page, size=size)

    async def get_student(self, user_id: uuid.UUID) -> User:
        user = await self._users.get_by_id(user_id)
        if user is None or user.role != "CUSTOMER" or user.deleted_at is not None:
            raise NotFoundError("Student does not exist")
        return user

    async def update_student(self, user_id: uuid.UUID, *, full_name: str | None) -> User:
        user = await self.get_student(user_id)
        if full_name is not None:
            user.full_name = full_name
        await self._users.save(user)
        return user

    async def set_status(self, user_id: uuid.UUID, *, status: str) -> User:
        user = await self.get_student(user_id)
        user.status = status
        await self._users.save(user)
        # TODO(T26): publish account.locked / account.unlocked once the event
        # contract (T04, owned by Duc) exists. Not wired yet — this task is
        # scoped to the CRUD screen only.
        return user

    async def set_vip(
        self, user_id: uuid.UUID, *, is_vip: bool, vip_expired_at: datetime | None
    ) -> User:
        user = await self.get_student(user_id)
        user.is_vip = is_vip
        user.vip_expired_at = vip_expired_at if is_vip else None
        await self._users.save(user)
        return user

    async def delete_student(self, user_id: uuid.UUID) -> None:
        user = await self.get_student(user_id)
        user.deleted_at = datetime.now(UTC)
        await self._users.save(user)
