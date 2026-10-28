"""Forgot/reset password — email-based, SMTP via account.email.

Security notes, both deliberate:
- request_reset never reveals whether an email is registered (same
  response either way) — a different response would let anyone enumerate
  registered emails by probing this endpoint.
- Only the token's SHA-256 hash is stored; the raw token exists only in
  the emailed link (same principle as refresh-token jti revocation, see
  pbl6_common.security). A token is single-use (`used_at`) and expires
  after 1 hour.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from pbl6_common.errors import UnauthorizedError
from pbl6_common.security import hash_password

from account.config import AccountSettings
from account.email import EmailSenderProtocol
from account.repositories.protocols import PasswordResetRepositoryProtocol, UserRepositoryProtocol

RESET_TOKEN_TTL = timedelta(hours=1)


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


class PasswordResetService:
    def __init__(
        self,
        users: UserRepositoryProtocol,
        tokens: PasswordResetRepositoryProtocol,
        email_sender: EmailSenderProtocol,
        settings: AccountSettings,
    ):
        self._users = users
        self._tokens = tokens
        self._email_sender = email_sender
        self._settings = settings

    async def request_reset(self, email: str) -> None:
        user = await self._users.get_by_email(email)
        if user is None:
            return  # don't leak whether this email is registered

        raw_token = secrets.token_urlsafe(32)
        await self._tokens.create(
            user_id=user.id,
            token_hash=_hash_token(raw_token),
            expires_at=datetime.now(UTC) + RESET_TOKEN_TTL,
        )

        reset_link = f"{self._settings.frontend_base_url}/reset-password?token={raw_token}"
        await self._email_sender.send(
            to=user.email,
            subject="Đặt lại mật khẩu — English Self-Study",
            body=(
                f"Chào {user.full_name},\n\n"
                "Bạn (hoặc ai đó) vừa yêu cầu đặt lại mật khẩu cho tài khoản English "
                "Self-Study này. Nhấn vào liên kết bên dưới để đặt mật khẩu mới "
                "(liên kết hết hạn sau 1 giờ):\n\n"
                f"{reset_link}\n\n"
                "Nếu bạn không yêu cầu điều này, hãy bỏ qua email này — mật khẩu "
                "của bạn vẫn an toàn.\n\n"
                "— English Self-Study"
            ),
        )

    async def reset_password(self, *, token: str, new_password: str) -> None:
        entry = await self._tokens.get_valid(_hash_token(token))
        if entry is None:
            raise UnauthorizedError("Invalid or expired reset token")

        user = await self._users.get_by_id(entry.user_id)
        if user is None:
            raise UnauthorizedError("Invalid or expired reset token")

        user.password_hash = hash_password(new_password)
        await self._users.save(user)
        await self._tokens.mark_used(entry)
