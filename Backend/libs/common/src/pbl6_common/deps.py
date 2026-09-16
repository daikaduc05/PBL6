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

from dataclasses import dataclass

from fastapi import Depends, Header

from pbl6_common.errors import ForbiddenError, UnauthorizedError


@dataclass(frozen=True)
class UserContext:
    user_id: str
    roles: list[str]
    tier: str


async def get_current_user(
    x_user_id: str | None = Header(default=None),
    x_user_roles: str | None = Header(default=None),
    x_user_tier: str | None = Header(default=None),
) -> UserContext:
    if not x_user_id:
        raise UnauthorizedError("missing authenticated user context")
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
