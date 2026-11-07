"""T31 — outbox pattern. A row here is written in the SAME DB transaction
as the `transactions` status update (see CheckoutService/WebhookService),
so "transaction became SUCCESS" and "there is an event to publish" either
both commit or both roll back together. The relay worker
(payment.outbox.relay) is a separate process step that reads unpublished
rows and puts them on RabbitMQ — see that module for the at-least-once
story.

Reintroduces the `outbox` table backend.md §5 originally specified, which
the simplified ER diagram dropped (see Backend/db/04_payment.sql's old
comment: "If you keep the outbox pattern later, add it here" — this is
that later).
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
    __table_args__ = ({"schema": "payment"},)

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
