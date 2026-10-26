"""T23 business logic — admin management of student (role=CUSTOMER) accounts.

Editor accounts have a separate screen (T24) with their own service; this
one deliberately only ever touches role=CUSTOMER rows so it can't be used
as a side door to lock/promote an editor or admin account.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from pbl6_common.errors import NotFoundError

from account.events.publisher import EventPublisherProtocol
from account.models.user import User
from account.repositories.protocols import UserRepositoryProtocol


class AdminUserService:
    def __init__(self, users: UserRepositoryProtocol, publisher: EventPublisherProtocol):
        self._users = users
        self._publisher = publisher

    async def list_students(
        self, *, page: int, size: int, status: str | None = None, q: str | None = None
    ) -> tuple[list[User], int]:
        return await self._users.list_by_role(
            role="CUSTOMER", page=page, size=size, status=status, q=q
        )

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

    async def set_status(
        self,
        user_id: uuid.UUID,
        *,
        status: str,
        locked_by: uuid.UUID | None = None,
        reason: str | None = None,
    ) -> User:
        user = await self.get_student(user_id)
        previous_status = user.status
        user.status = status
        await self._users.save(user)

        # Only the LOCKED boundary is in the event contract (backend.md §6)
        # — a plain ACTIVE<->INACTIVE toggle isn't account.locked/unlocked.
        if status == "LOCKED" and previous_status != "LOCKED":
            await self._publisher.publish(
                "account.locked",
                {
                    "user_id": str(user_id),
                    "locked_by": str(locked_by) if locked_by else None,
                    "reason": reason,
                },
            )
        elif status != "LOCKED" and previous_status == "LOCKED":
            await self._publisher.publish("account.unlocked", {"user_id": str(user_id)})

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
