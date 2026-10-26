"""T26 — grants/extends VIP from a consumed `payment.succeeded` event.

Idempotent by construction: `already_processed` is checked first (cheap,
avoids re-granting on the common case), but the real guarantee is the
primary key on `processed_events.event_id` — if two deliveries of the same
event somehow race past that check, the loser's `mark_processed` insert
raises `IntegrityError`, the caller's transaction rolls back, and nothing
is double-applied. See ProcessedEventRepository's docstring.

VIP time stacks rather than resets: a user who is already VIP with time
left gets `duration_days` added on top of their current expiry; a
lapsed/non-VIP user gets `duration_days` from now. This matters for anyone
who buys a second plan before their first one runs out.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from account.repositories.processed_event_repository import ProcessedEventRepository
from account.repositories.user_repository import UserRepository
from sqlalchemy.exc import IntegrityError


class VipGrantService:
    def __init__(self, users: UserRepository, processed_events: ProcessedEventRepository):
        self._users = users
        self._processed_events = processed_events

    async def handle_payment_succeeded(
        self, *, event_id: uuid.UUID, event_type: str, user_id: uuid.UUID, duration_days: int
    ) -> None:
        if await self._processed_events.already_processed(event_id):
            return  # redelivery of an event we've already applied — no-op

        user = await self._users.get_by_id(user_id)
        if user is None:
            # Shouldn't happen (account owns user_id, payment just stores
            # the UUID) but a payment for a since-deleted user shouldn't
            # crash-loop the consumer forever — log via the caller's retry
            # path and move on once it DLQs.
            raise LookupError(f"payment.succeeded for unknown user_id={user_id}")

        now = datetime.now(UTC)
        has_time_left = user.is_vip and user.vip_expired_at and user.vip_expired_at > now
        base = user.vip_expired_at if has_time_left else now
        user.is_vip = True
        user.vip_expired_at = base + timedelta(days=duration_days)
        await self._users.save(user)

        try:
            await self._processed_events.mark_processed(event_id=event_id, event_type=event_type)
        except IntegrityError:
            # Lost a race with a concurrent delivery of the same event —
            # the caller's transaction rolls back, so the VIP mutation
            # above never persists either. Treat as already-handled.
            pass
