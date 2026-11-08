"""T16 — function 8.2: turn an event from another service into a notification.

One envelope comes in; the outcome is a row in ``notification.messages`` (the
in-app channel) and, for a payment, a confirmation email. The interesting work
is not the translation table — it is deciding what failure means:

* **Duplicate delivery** is normal, not an error. The payment relay is
  at-least-once, so the same event_id can arrive twice; the ledger check (and
  the primary key behind it) makes the second arrival a silent no-op.
* **A payload that fails validation is a permanent failure.** Retrying replays
  the same bytes, so the handler raises to let the shared consumer bounce it
  to the DLQ where a human can look at it — acking would silently swallow a
  contract violation, and that is how two teams drift apart unnoticed.
* **An unknown event_type is not a failure at all** (backend.md §6: a consumer
  ignores what it does not recognise). New event types must be deployable
  producer-first without crash-looping every consumer that has not caught up.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol
from zoneinfo import ZoneInfo

from pbl6_common.events import EventEnvelope
from pydantic import BaseModel, ValidationError

from notification.models.message import MessageType
from notification.repositories.external_reader import ActiveUser

logger = logging.getLogger(__name__)


class MessageWriter(Protocol):
    async def create(
        self, *, user_id: uuid.UUID, title: str, content: str, type: MessageType
    ) -> Any: ...


class ProcessedLedger(Protocol):
    async def already_processed(self, event_id: uuid.UUID) -> bool: ...

    async def mark_processed(self, *, event_id: uuid.UUID, event_type: str) -> None: ...


class UserDirectory(Protocol):
    async def user(self, user_id: uuid.UUID) -> ActiveUser | None: ...


# --- payload shapes ---------------------------------------------------------
# The envelope's own five fields are validated by pbl6_common before the
# handler ever runs; `data` is typed dict[str, Any] there, so each event type
# re-validates its inside here. Extra fields pass through untouched — the
# contract lets a producer add fields without breaking old consumers.


class PaymentSucceededData(BaseModel):
    user_id: uuid.UUID
    plan_id: str
    amount_vnd: float
    duration_days: int


class VipExpiredData(BaseModel):
    user_id: uuid.UUID
    expired_at: datetime


class AccountLockedData(BaseModel):
    user_id: uuid.UUID
    reason: str | None = None


class AccountUnlockedData(BaseModel):
    user_id: uuid.UUID


class MalformedEventError(Exception):
    """The payload violates the event contract (backend.md §6).

    Permanent: the same bytes will fail validation on every redelivery. The
    shared consumer treats any raise as retryable, so this still bounces
    through the retry queue before landing in the DLQ — an accepted 15 seconds
    of noise in exchange for not extending pbl6_common with a second failure
    channel only this service would use.
    """


@dataclass(frozen=True)
class EmailPlan:
    """An email the caller should send AFTER the DB transaction commits.

    Returned as data rather than sent here so the transaction boundary stays
    with the wiring: a mail sent before commit could announce a notification
    that then rolls back.
    """

    to: str
    template: str
    context: dict[str, Any]


class EventHandlerService:
    """Session-scoped: build one per message, like the other services."""

    def __init__(
        self,
        *,
        messages: MessageWriter,
        ledger: ProcessedLedger,
        users: UserDirectory,
        display_timezone: str = "Asia/Ho_Chi_Minh",
    ) -> None:
        self._messages = messages
        self._ledger = ledger
        self._users = users
        self._tz = ZoneInfo(display_timezone)

    async def apply(self, envelope: EventEnvelope) -> EmailPlan | None:
        """Write this event's notification; return the email still owed, if any.

        The caller owns the session and commits after this returns. Everything
        written here — the message and the ledger row — therefore lands in one
        transaction, which is the entire dedupe guarantee: if two deliveries
        race, the loser's ledger INSERT hits the primary key and its whole
        transaction (duplicate notification included) rolls back.
        """
        if await self._ledger.already_processed(envelope.event_id):
            logger.info("events: %s already processed, skipping", envelope.event_id)
            return None

        try:
            plan = await self._apply_by_type(envelope)
        except (ValidationError, ValueError) as exc:
            raise MalformedEventError(f"{envelope.event_type} {envelope.event_id}: {exc}") from exc

        if plan is _UNKNOWN:
            logger.info("events: ignoring unrecognised event_type %s", envelope.event_type)
            return None

        await self._ledger.mark_processed(
            event_id=envelope.event_id, event_type=envelope.event_type
        )
        return plan if isinstance(plan, EmailPlan) else None

    async def _apply_by_type(self, envelope: EventEnvelope) -> EmailPlan | None | object:
        data = envelope.data
        match envelope.event_type:
            case "payment.succeeded":
                return await self._payment_succeeded(PaymentSucceededData(**data))
            case "vip.expired":
                return await self._vip_expired(VipExpiredData(**data))
            case "account.locked":
                return await self._account_locked(AccountLockedData(**data))
            case "account.unlocked":
                return await self._account_unlocked(AccountUnlockedData(**data))
            case _:
                return _UNKNOWN

    # --- one method per event type ------------------------------------------

    async def _payment_succeeded(self, data: PaymentSucceededData) -> EmailPlan | None:
        plan_name = PLAN_NAMES.get(data.plan_id, data.plan_id)
        await self._messages.create(
            user_id=data.user_id,
            title="Thanh toán thành công",
            # Same deliberate wording as the email template: VIP is flipped by
            # the account service consuming this same event, possibly seconds
            # later, so "sẽ được kích hoạt" rather than "đã là VIP".
            content=(
                f"Gói {plan_name} ({data.duration_days} ngày) đã được thanh toán "
                f"{data.amount_vnd:,.0f}đ. Quyền VIP sẽ được kích hoạt trong ít phút."
            ),
            type=MessageType.PAYMENT_SUCCEEDED,
        )

        user = await self._users.user(data.user_id)
        if user is None:
            # The in-app row above still stands — it has no FK and the user_id
            # may simply not be visible to us (deleted since). Only the email
            # is impossible without an address.
            logger.warning("events: no account row for %s, skipping email", data.user_id)
            return None
        return EmailPlan(
            to=user.email,
            template="vip_confirmed",
            context={
                "full_name": user.full_name,
                "amount_vnd": data.amount_vnd,
                "plan_name": plan_name,
                "duration_days": data.duration_days,
            },
        )

    async def _vip_expired(self, data: VipExpiredData) -> EmailPlan | None:
        # expired_at arrives in UTC (timestamptz through the relay); shown to
        # a person it must be their wall clock or "hết hạn lúc 17:00" reads as
        # seven hours early.
        local = data.expired_at.astimezone(self._tz)
        await self._messages.create(
            user_id=data.user_id,
            title="Gói VIP đã hết hạn",
            content=(
                f"Gói VIP của bạn đã hết hạn lúc {local:%H:%M ngày %d/%m/%Y}. "
                "Gia hạn để tiếp tục học kho bài VIP nhé."
            ),
            type=MessageType.VIP_EXPIRED,
        )
        return None

    async def _account_locked(self, data: AccountLockedData) -> EmailPlan | None:
        detail = f" Lý do: {data.reason}." if data.reason else ""
        await self._messages.create(
            user_id=data.user_id,
            title="Tài khoản đã bị khoá",
            content=(
                "Tài khoản của bạn đã bị quản trị viên khoá."
                + detail
                + " Liên hệ hỗ trợ nếu bạn cho rằng đây là nhầm lẫn."
            ),
            type=MessageType.ACCOUNT_LOCKED,
        )
        return None

    async def _account_unlocked(self, data: AccountUnlockedData) -> EmailPlan | None:
        await self._messages.create(
            user_id=data.user_id,
            title="Tài khoản đã được mở khoá",
            content="Tài khoản của bạn đã hoạt động trở lại. Chào mừng bạn quay lại học!",
            type=MessageType.ACCOUNT_UNLOCKED,
        )
        return None


# Sentinel distinguishing "event type we don't handle" from "handled, no email".
_UNKNOWN = object()

# Display names for payment plan codes. The code itself is the fallback, so an
# unknown new plan degrades to ugly-but-correct rather than crashing or lying.
PLAN_NAMES: dict[str, str] = {
    "VIP_1_MONTH": "VIP 1 tháng",
    "VIP_3_MONTHS": "VIP 3 tháng",
    "VIP_12_MONTHS": "VIP 12 tháng",
}
