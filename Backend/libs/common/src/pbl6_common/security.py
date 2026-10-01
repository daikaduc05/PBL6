"""Password hashing, JWT issuing/verification, and the Redis refresh-token
denylist (backend.md §4: "Redis | ... refresh-token denylist").

Refresh tokens stay stateless JWTs (no DB table) — revocation on logout and
rotation-on-use are done by adding the token's `jti` to a Redis denylist
with a TTL matching the token's remaining lifetime. A refresh token is only
valid if it verifies AND its `jti` is absent from the denylist.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import bcrypt
from jose import JWTError, jwt
from redis.asyncio import Redis

_BCRYPT_ROUNDS = 12
_BCRYPT_MAX_BYTES = 72  # hard limit of the bcrypt algorithm itself


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    password_bytes = password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    return bcrypt.checkpw(password_bytes, password_hash.encode("ascii"))


class InvalidTokenError(ValueError):
    """Raised for an expired, malformed, or revoked token."""


def create_access_token(
    *, subject: str, roles: list[str], tier: str, secret: str, algorithm: str, minutes: int
) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "roles": roles,
        "tier": tier,
        "iat": now,
        "exp": now + timedelta(minutes=minutes),
        "jti": str(uuid4()),
        "type": "access",
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


def create_refresh_token(*, subject: str, secret: str, algorithm: str, days: int) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(days=days),
        "jti": str(uuid4()),
        "type": "refresh",
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


def decode_token(token: str, *, secret: str, algorithm: str, expected_type: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, secret, algorithms=[algorithm])
    except JWTError as exc:
        raise InvalidTokenError("token is malformed or expired") from exc
    if payload.get("type") != expected_type:
        raise InvalidTokenError(f"expected a {expected_type} token")
    return payload


class RefreshTokenDenylist:
    """Redis-backed set of revoked refresh-token `jti`s."""

    _PREFIX = "revoked_refresh_jti:"

    def __init__(self, redis: Redis):
        self._redis = redis

    async def revoke(self, jti: str, *, ttl_seconds: int) -> None:
        if ttl_seconds > 0:
            await self._redis.set(self._PREFIX + jti, "1", ex=ttl_seconds)

    async def is_revoked(self, jti: str) -> bool:
        return bool(await self._redis.exists(self._PREFIX + jti))


def seconds_until(exp_timestamp: float) -> int:
    remaining = int(exp_timestamp - datetime.now(UTC).timestamp())
    return max(remaining, 0)
