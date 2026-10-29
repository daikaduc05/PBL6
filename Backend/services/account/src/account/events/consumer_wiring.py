"""T26 — wires the generic consumer (pbl6_common.events) to this service's
`payment.succeeded` handling. Runs as a background asyncio task started
from main.py's lifespan; each message gets its own DB session/transaction
so one message's failure can't corrupt another's state.
"""

from __future__ import annotations

import logging
import uuid

from pbl6_common.events import EventEnvelope
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from account.repositories.processed_event_repository import ProcessedEventRepository
from account.repositories.user_repository import UserRepository
from account.services.vip_grant_service import VipGrantService

logger = logging.getLogger(__name__)

QUEUE_NAME = "account.events"
ROUTING_KEYS = ["payment.succeeded"]


def make_payment_succeeded_handler(session_factory: async_sessionmaker[AsyncSession]):
    async def handle(envelope: EventEnvelope) -> None:
        if envelope.event_type != "payment.succeeded":
            logger.info("account.events: ignoring unrecognised event_type %s", envelope.event_type)
            return

        data = envelope.data
        async with session_factory() as session:
            service = VipGrantService(
                users=UserRepository(session),
                processed_events=ProcessedEventRepository(session),
            )
            await service.handle_payment_succeeded(
                event_id=envelope.event_id,
                event_type=envelope.event_type,
                user_id=uuid.UUID(str(data["user_id"])),
                duration_days=int(data["duration_days"]),
            )
            await session.commit()

    return handle
