"""Idempotency ledger for the RabbitMQ consumer (T16, function 8.2).

``event_id`` is the primary key *because* that is the dedupe mechanism. The
consumer inserts this row in the same transaction as the message it produces,
so a redelivered event hits the key, the transaction rolls back, and the
duplicate is acked with no side effect.

Needed because the payment outbox relay is at-least-once: a crash between
publish and mark-published makes RabbitMQ deliver the same event again, and
without this table the user would see "VIP activated" twice for one payment.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pbl6_common.db import Base
from sqlalchemy import DateTime, Index, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class ProcessedEvent(Base):
    __tablename__ = "processed_events"
    __table_args__ = (
        Index("processed_events_processed_at_idx", "processed_at"),
        {"schema": "notification"},
    )

    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
