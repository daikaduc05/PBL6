"""Transactional Outbox model for Account Service (`account.outbox`).

Ensures `account.locked`, `account.unlocked`, and `vip.expired` events are
persisted atomically in the same database transaction as the `account.users`
mutation, preventing event loss if RabbitMQ is unreachable right after commit.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pbl6_common.db import Base
from sqlalchemy import DateTime, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column


class OutboxEntry(Base):
    __tablename__ = "outbox"
    __table_args__ = ({"schema": "account"},)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    aggregate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
