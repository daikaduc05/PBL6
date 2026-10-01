"""T22 business logic — view/edit own profile, change password."""

from __future__ import annotations

import uuid

from account.models.user import User
from account.repositories.user_repository import UserRepository
from pbl6_common.errors import NotFoundError, UnauthorizedError
from pbl6_common.security import hash_password, verify_password


class UserService:
    def __init__(self, users: UserRepository):
        self._users = users

    async def get_profile(self, user_id: uuid.UUID) -> User:
        user = await self._users.get_by_id(user_id)
        if user is None:
            # The JWT was valid but the account no longer exists (deleted
            # after the token was issued) — surfaced as 404, not 401.
            raise NotFoundError("User does not exist")
        return user

    async def update_profile(self, user_id: uuid.UUID, *, full_name: str) -> User:
        user = await self.get_profile(user_id)
        user.full_name = full_name
        await self._users.save(user)
        return user

    async def change_password(
        self, user_id: uuid.UUID, *, current_password: str, new_password: str
    ) -> None:
        user = await self.get_profile(user_id)
        if not verify_password(current_password, user.password_hash):
            raise UnauthorizedError("Current password is incorrect")
        user.password_hash = hash_password(new_password)
        await self._users.save(user)
        # Note: this does not revoke other active sessions — the refresh-token
        # denylist only tracks revoked jti's, not a per-user allowlist, so we
        # cannot invalidate "every other session" without one. Acceptable for
        # T22's scope; revisit if a security review asks for it.
