"""T24 business logic — admin management of Editor accounts.

Editors don't self-register: an admin creates the account directly, and
that creation *is* the RBAC grant (role=EDITOR at creation time — this
project's RBAC is a single role column per backend.md's data model, not a
separate permission table).

Only ever touches role=EDITOR rows, mirroring T23's boundary for CUSTOMER
rows — neither screen can be used to reach into the other's accounts.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from pbl6_common.errors import ConflictError, NotFoundError
from pbl6_common.security import hash_password

from account.models.user import User
from account.repositories.protocols import UserRepositoryProtocol


class AdminEditorService:
    def __init__(self, users: UserRepositoryProtocol):
        self._users = users

    async def create_editor(self, *, email: str, password: str, full_name: str) -> User:
        existing = await self._users.get_by_email(email)
        if existing is not None:
            raise ConflictError("An account with this email already exists")
        return await self._users.create(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            role="EDITOR",
        )

    async def list_editors(
        self, *, page: int, size: int, status: str | None = None, q: str | None = None
    ) -> tuple[list[User], int]:
        return await self._users.list_by_role(
            role="EDITOR", page=page, size=size, status=status, q=q
        )

    async def get_editor(self, user_id: uuid.UUID) -> User:
        user = await self._users.get_by_id(user_id)
        if user is None or user.role != "EDITOR" or user.deleted_at is not None:
            raise NotFoundError("Editor does not exist")
        return user

    async def update_editor(self, user_id: uuid.UUID, *, full_name: str | None) -> User:
        user = await self.get_editor(user_id)
        if full_name is not None:
            user.full_name = full_name
        await self._users.save(user)
        return user

    async def set_status(self, user_id: uuid.UUID, *, status: str) -> User:
        user = await self.get_editor(user_id)
        user.status = status
        await self._users.save(user)
        return user

    async def delete_editor(self, user_id: uuid.UUID) -> None:
        user = await self.get_editor(user_id)
        user.deleted_at = datetime.now(UTC)
        await self._users.save(user)
