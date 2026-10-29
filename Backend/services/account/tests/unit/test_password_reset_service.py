"""Unit tests: repository/email sender are fakes — no database, no network
(backend.md §9 testing approach)."""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime, timedelta

import pytest
from account.config import AccountSettings
from account.services.password_reset_service import PasswordResetService
from fakes import FakeEmailSender, FakePasswordResetRepository, FakeUserRepository
from pbl6_common.errors import UnauthorizedError
from pbl6_common.security import verify_password


def make_settings() -> AccountSettings:
    return AccountSettings(
        database_url="postgresql+asyncpg://unused/unused",
        jwt_secret="test-secret-test-secret-test-secret",
        frontend_base_url="http://localhost:3000",
    )


def make_service() -> tuple[
    PasswordResetService, FakeUserRepository, FakePasswordResetRepository, FakeEmailSender
]:
    users = FakeUserRepository()
    tokens = FakePasswordResetRepository()
    email_sender = FakeEmailSender()
    service = PasswordResetService(
        users=users, tokens=tokens, email_sender=email_sender, settings=make_settings()
    )
    return service, users, tokens, email_sender


def _extract_token(body: str) -> str:
    match = re.search(r"token=([^\s]+)", body)
    assert match is not None
    return match.group(1)


@pytest.mark.asyncio
async def test_request_reset_sends_email_with_token_link():
    service, users, _, email_sender = make_service()
    user = users.seed(email="a@b.com")

    await service.request_reset("a@b.com")

    assert len(email_sender.sent) == 1
    sent = email_sender.sent[0]
    assert sent["to"] == user.email
    assert "http://localhost:3000/reset-password?token=" in sent["body"]


@pytest.mark.asyncio
async def test_request_reset_is_noop_for_unknown_email():
    service, _, _, email_sender = make_service()

    await service.request_reset("nobody@example.com")

    assert email_sender.sent == []


@pytest.mark.asyncio
async def test_reset_password_with_valid_token_updates_password():
    service, users, _, email_sender = make_service()
    users.seed(email="a@b.com")

    await service.request_reset("a@b.com")
    token = _extract_token(email_sender.sent[0]["body"])

    await service.reset_password(token=token, new_password="newpassword123")

    user = await users.get_by_email("a@b.com")
    assert user is not None
    assert verify_password("newpassword123", user.password_hash)


@pytest.mark.asyncio
async def test_reset_password_rejects_unknown_token():
    service, *_ = make_service()

    with pytest.raises(UnauthorizedError):
        await service.reset_password(token="not-a-real-token", new_password="newpassword123")


@pytest.mark.asyncio
async def test_reset_password_rejects_already_used_token():
    service, users, _, email_sender = make_service()
    users.seed(email="a@b.com")

    await service.request_reset("a@b.com")
    token = _extract_token(email_sender.sent[0]["body"])

    await service.reset_password(token=token, new_password="newpassword123")

    with pytest.raises(UnauthorizedError):
        await service.reset_password(token=token, new_password="anotherpassword456")


@pytest.mark.asyncio
async def test_reset_password_rejects_expired_token():
    service, users, tokens, _ = make_service()
    user = users.seed(email="a@b.com")

    raw_token = "expired-raw-token"
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    await tokens.create(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(UTC) - timedelta(hours=1),
    )

    with pytest.raises(UnauthorizedError):
        await service.reset_password(token=raw_token, new_password="newpassword123")
