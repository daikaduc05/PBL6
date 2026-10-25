"""T27 — daily VIP expiry sweep (backend.md §4: "VIP expiry sweep 00:00").

Finds every VIP user whose `vip_expired_at` has already passed, revokes
their VIP, and publishes `vip.expired` (backend.md §6: `{user_id,
expired_at}`) so notification can tell them. Same best-effort, non-outboxed
publish as account.locked/unlocked (T26) — this is account's own bookkeeping
event, not a money-critical state transition.

Clearing `vip_expired_at` to null on expiry matches the column's own
invariant (account.users.vip_expired_at: "Null when not VIP").
"""

from __future__ import annotations

from datetime import UTC, datetime

from account.events.publisher import EventPublisherProtocol
from account.repositories.user_repository import UserRepository


class VipExpiryService:
    def __init__(self, users: UserRepository, publisher: EventPublisherProtocol):
        self._users = users
        self._publisher = publisher

    async def sweep(self) -> int:
        """Revokes VIP for every lapsed user found in one batch. Returns
        how many were revoked (0 is the common case — most ticks find
        nothing to do)."""
        now = datetime.now(UTC)
        expired_users = await self._users.list_expired_vip(now=now)

        for user in expired_users:
            expired_at = user.vip_expired_at
            user.is_vip = False
            user.vip_expired_at = None
            await self._users.save(user)
            await self._publisher.publish(
                "vip.expired",
                {
                    "user_id": str(user.id),
                    "expired_at": expired_at.isoformat() if expired_at else now.isoformat(),
                },
            )

        return len(expired_users)
