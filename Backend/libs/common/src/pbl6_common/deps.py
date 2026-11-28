"""Auth dependencies shared by every service.

backend.md §7: the gateway verifies the JWT once and forwards
`X-User-Id` / `X-User-Roles` / `X-User-Tier` / `X-Request-Id` downstream.
Services trust those headers only because they are unreachable from
outside the Docker network — they still re-check role/tier per endpoint
with `require_role`/`require_vip` below.

`get_db` is service-specific (bound to that service's own engine) —
see `pbl6_common.db.make_get_db`. This module only has the auth pieces.
"""

from __future__ import annotations

import hmac
import os
from dataclasses import dataclass

from fastapi import Depends, Header

from pbl6_common.errors import ForbiddenError, UnauthorizedError

DEFAULT_INTERNAL_SECRET = "pbl6-internal-gateway-secret"


def verify_internal_secret(
    x_internal_secret: str | None = Header(default=None),
) -> None:
    """Verifies the shared secret between the BFF Gateway / peer services and
    this microservice.

    When `ENFORCE_INTERNAL_SECRET=true` (or `ENV` is not in `("local", "test", "ci")`):
    - Rejects startup/request if `INTERNAL_API_SECRET` is missing or still uses
      the public default placeholder `"pbl6-internal-gateway-secret"`.
    - Rejects any request whose `X-Internal-Secret` header is missing or does
      not match `INTERNAL_API_SECRET`.
    """
    env = os.getenv("ENV", "local").lower()
    is_non_prod = env in ("local", "test", "testing", "ci", "dev", "development")
    enforce = (
        os.getenv("ENFORCE_INTERNAL_SECRET", "false").lower() in ("true", "1", "yes")
        or not is_non_prod
    )
    expected = os.getenv("INTERNAL_API_SECRET", DEFAULT_INTERNAL_SECRET if is_non_prod else "")

    if enforce:
        if not expected or (not is_non_prod and expected == DEFAULT_INTERNAL_SECRET):
            raise UnauthorizedError("internal gateway secret is not securely configured")
        if not x_internal_secret or not hmac.compare_digest(x_internal_secret, expected):
            raise UnauthorizedError("invalid or missing internal gateway secret")
    elif x_internal_secret is not None:
        if not expected or not hmac.compare_digest(x_internal_secret, expected):
            raise UnauthorizedError("invalid or missing internal gateway secret")


@dataclass(frozen=True)
class UserContext:
    user_id: str
    roles: list[str]
    tier: str


async def get_current_user(
    x_user_id: str | None = Header(default=None),
    x_user_roles: str | None = Header(default=None),
    x_user_tier: str | None = Header(default=None),
    _secret_check: None = Depends(verify_internal_secret),
) -> UserContext:
    if not x_user_id:
        raise UnauthorizedError("missing authenticated user context")
    roles = [r.strip() for r in (x_user_roles or "").split(",") if r.strip()]
    return UserContext(user_id=x_user_id, roles=roles, tier=x_user_tier or "normal")


async def get_optional_user(
    x_user_id: str | None = Header(default=None),
    x_user_roles: str | None = Header(default=None),
    x_user_tier: str | None = Header(default=None),
    _secret_check: None = Depends(verify_internal_secret),
) -> UserContext | None:
    if not x_user_id:
        return None
    roles = [r.strip() for r in (x_user_roles or "").split(",") if r.strip()]
    return UserContext(user_id=x_user_id, roles=roles, tier=x_user_tier or "normal")


def require_role(*allowed_roles: str):
    """Returns a dependency: 403s unless the caller has one of the roles.

    Usage: `Depends(require_role("admin", "editor"))`.
    """

    async def dependency(user: UserContext = Depends(get_current_user)) -> UserContext:
        if not set(user.roles) & set(allowed_roles):
            raise ForbiddenError(f"requires one of roles: {', '.join(allowed_roles)}")
        return user

    return dependency


async def require_vip(user: UserContext = Depends(get_current_user)) -> UserContext:
    """403s unless the caller's tier is 'vip'. Usage: `Depends(require_vip)`."""
    if user.tier != "vip":
        raise ForbiddenError("VIP content requires an active VIP subscription")
    return user
