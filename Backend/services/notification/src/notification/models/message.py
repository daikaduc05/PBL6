"""Maps 1:1 onto notification.messages, created by Backend/db/05_notification.sql.

Alembic's baseline migration mirrors this table — the live table predates
Alembic here, so the two are kept in sync by hand (same arrangement as
account.users).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from pbl6_common.db import Base
from sqlalchemy import Boolean, DateTime, Index, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class MessageType(StrEnum):
    """What produced this notification.

    Values mirror the routing keys in backend.md §6 one-for-one, so a consumer
    writes ``envelope.event_type`` through without a lookup table in between.

    Why a column rather than reading the kind back out of ``title``: the title
    is display copy that anyone may reword at any time, and every rule keyed on
    its text breaks silently when they do. The reminder's own
    already-sent-today check used to match on the title string — reword it and
    the check matches nothing, so every learner is reminded once an hour
    instead of once a day, with no error anywhere to show for it.

    Deliberately one value per event type rather than coarse buckets like
    PAYMENT or ACCOUNT: a client can always group these, but nothing can
    split a bucket back apart after the fact.
    """

    STUDY_REMINDER = "STUDY_REMINDER"
    PAYMENT_SUCCEEDED = "PAYMENT_SUCCEEDED"
    VIP_EXPIRED = "VIP_EXPIRED"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    ACCOUNT_UNLOCKED = "ACCOUNT_UNLOCKED"
    LESSON_PUBLISHED = "LESSON_PUBLISHED"


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        Index(
            "messages_user_unread_idx",
            "user_id",
            text("created_at DESC"),
            postgresql_where=text("is_read = false"),
        ),
        # Serves "my notifications, this kind only, newest first". The index
        # above is partial on unread rows and cannot answer it.
        Index("messages_user_type_idx", "user_id", "type", text("created_at DESC")),
        {"schema": "notification"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    # Logical FK to account.users.id — no constraint crosses a schema boundary.
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Text + CHECK rather than a Postgres enum, matching account.users.status
    # and payment.transactions.status. Adding a value is then one constraint
    # swap inside a normal migration, with no ALTER TYPE to schedule.
    type: Mapped[MessageType] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
