"""T21 business logic — the only layer allowed to be complex (backend.md §3).

Registration, login, refresh-token rotation and logout. Refresh tokens are
stateless JWTs revoked via the Redis denylist (see pbl6_common.security) —
there is no refresh_tokens table.
"""

from __future__ import annotations

from account.config import AccountSettings
from account.models.user import User
from account.repositories.user_repository import UserRepository
from account.schemas.auth import TokenPairResponse
from pbl6_common.errors import ConflictError, UnauthorizedError
from pbl6_common.security import (
    InvalidTokenError,
    RefreshTokenDenylist,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    seconds_until,
    verify_password,
)


class AuthService:
    def __init__(
        self,
        users: UserRepository,
        denylist: RefreshTokenDenylist,
        settings: AccountSettings,
    ):
        self._users = users
        self._denylist = denylist
        self._settings = settings

    async def register(self, *, email: str, password: str, full_name: str) -> User:
        existing = await self._users.get_by_email(email)
        if existing is not None:
            raise ConflictError("An account with this email already exists")
        user = await self._users.create(
            email=email, password_hash=hash_password(password), full_name=full_name
        )
        return user

    async def authenticate(self, *, email: str, password: str) -> User:
        user = await self._users.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")
        if user.status == "LOCKED":
            raise UnauthorizedError("This account has been locked")
        if user.status == "INACTIVE":
            raise UnauthorizedError("This account is inactive")
        return user

    def issue_token_pair(self, user: User) -> TokenPairResponse:
        s = self._settings
        access_token = create_access_token(
            subject=str(user.id),
            roles=[user.role],
            tier="vip" if user.is_vip else "normal",
            secret=s.jwt_secret,
            algorithm=s.jwt_algorithm,
            minutes=s.access_token_minutes,
        )
        refresh_token = create_refresh_token(
            subject=str(user.id),
            secret=s.jwt_secret,
            algorithm=s.jwt_algorithm,
            days=s.refresh_token_days,
        )
        return TokenPairResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=s.access_token_minutes * 60,
        )

    async def refresh(self, refresh_token: str) -> TokenPairResponse:
        s = self._settings
        try:
            payload = decode_token(
                refresh_token,
                secret=s.jwt_secret,
                algorithm=s.jwt_algorithm,
                expected_type="refresh",
            )
        except InvalidTokenError as exc:
            raise UnauthorizedError("Refresh token is invalid or expired") from exc

        jti, exp, subject = payload["jti"], payload["exp"], payload["sub"]
        if await self._denylist.is_revoked(jti):
            raise UnauthorizedError("Refresh token has already been used or revoked")

        user = await self._users.get_by_id(subject)
        if user is None or user.status != "ACTIVE":
            raise UnauthorizedError("Account is no longer active")

        # Rotate: this refresh token can never be used again.
        await self._denylist.revoke(jti, ttl_seconds=seconds_until(exp))
        return self.issue_token_pair(user)

    async def logout(self, refresh_token: str) -> None:
        s = self._settings
        try:
            payload = decode_token(
                refresh_token,
                secret=s.jwt_secret,
                algorithm=s.jwt_algorithm,
                expected_type="refresh",
            )
        except InvalidTokenError:
            return  # already invalid/expired — logout is idempotent
        await self._denylist.revoke(payload["jti"], ttl_seconds=seconds_until(payload["exp"]))
