"""Request-scoped dependencies.

TODO(T02): replace with ``pbl6_common.deps`` once Đức's shared library lands.

The gateway verifies the JWT and forwards the identity as headers. Downstream
services trust those headers only because they are unreachable from outside the
Docker network (backend.md §7). Nothing here parses a token.
"""

import uuid
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header

from notification.errors import UnauthorizedError


@dataclass(frozen=True)
class CurrentUser:
    id: uuid.UUID
    roles: frozenset[str]
    is_vip: bool

    @property
    def is_admin(self) -> bool:
        return "ADMIN" in self.roles


async def get_current_user(
    x_user_id: Annotated[str | None, Header()] = None,
    x_user_roles: Annotated[str | None, Header()] = None,
    x_user_tier: Annotated[str | None, Header()] = None,
) -> CurrentUser:
    if not x_user_id:
        raise UnauthorizedError("Missing user context")

    try:
        user_id = uuid.UUID(x_user_id)
    except ValueError as exc:
        # A malformed header means the gateway is misconfigured, not that the
        # caller is unauthenticated — but either way the request cannot proceed.
        raise UnauthorizedError("Invalid user context") from exc

    roles = frozenset(r.strip().upper() for r in (x_user_roles or "").split(",") if r.strip())
    return CurrentUser(id=user_id, roles=roles, is_vip=(x_user_tier or "").lower() == "vip")


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
