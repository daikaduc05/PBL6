"""Wires the generic consumer (pbl6_common.events) to this service's handler.

Runs as a background asyncio task started from main.py's lifespan — same
arrangement as account's consumer and this service's own reminder scheduler.
Each message gets a fresh session and one transaction; the email, if any, goes
out only after that transaction commits.
"""

from __future__ import annotations

import logging

from pbl6_common.events import EventEnvelope
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from notification.events.handler import EventHandlerService
from notification.repositories.external_reader import ExternalReader
from notification.repositories.message_repository import MessageRepository
from notification.repositories.processed_event_repository import ProcessedEventRepository
from notification.services.email_service import EmailService

logger = logging.getLogger(__name__)

QUEUE_NAME = "notification.events"
# lesson.published stays unbound for now: content has no publisher yet, and
# "notify whom?" (every user? followers of the category?) is an undecided
# fan-out question — binding it today would just grow an unread queue.
ROUTING_KEYS = [
    "payment.succeeded",
    "vip.expired",
    "account.locked",
    "account.unlocked",
]


def make_event_handler(
    session_factory: async_sessionmaker[AsyncSession],
    email_service: EmailService,
    *,
    display_timezone: str = "Asia/Ho_Chi_Minh",
):
    async def handle(envelope: EventEnvelope) -> None:
        async with session_factory() as session:
            service = EventHandlerService(
                messages=MessageRepository(session),
                ledger=ProcessedEventRepository(session),
                users=ExternalReader(session),
                display_timezone=display_timezone,
            )
            email_plan = await service.apply(envelope)
            await session.commit()

        # After commit, deliberately: a crash right here loses an email (the
        # user still has the in-app row — recoverable), while sending before
        # commit could announce a notification that then rolls back. Same
        # ordering argument as the reminder job. EmailService never raises, so
        # a dead SMTP server cannot nack an event that was already applied.
        if email_plan is not None:
            await email_service.send(
                to=email_plan.to,
                template=email_plan.template,
                context=email_plan.context,
            )

    return handle
