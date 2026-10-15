"""ORM models mirroring the ``notification`` schema.

The DDL lives in ``Backend/db/05_notification.sql`` and
``Backend/db/06_notification_processed_events.sql`` and is applied through
Supabase — this project does not use Alembic (spec §0.2). These classes must
therefore follow the SQL, never the other way round, and ``Base.metadata
.create_all()`` is never called.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Text, func, text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from notification.db import Base

SCHEMA = "notification"


class Message(Base):
    """One in-app notification. Created by the API, the cron job and the consumer."""

    __tablename__ = "messages"
    __table_args__ = (
        Index(
            "messages_user_unread_idx",
            "user_id",
            text("created_at DESC"),
            postgresql_where=text("is_read = false"),
        ),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    # Logical FK to account.users.id — no cross-schema constraint by design.
    user_id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class NotificationSetting(Base):
    """Per-user preferences. Absent row means "all defaults" — see spec §A.3."""

    __tablename__ = "settings"
    __table_args__ = {"schema": SCHEMA}

    user_id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    enable_daily_reminder: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    device_token: Mapped[str | None] = mapped_column(Text, nullable=True)


class ProcessedEvent(Base):
    """Idempotency ledger for RabbitMQ consumers.

    ``event_id`` is the primary key *because* that is the dedupe mechanism: the
    consumer inserts this row in the same transaction as the message it
    produces, so a redelivered event hits the key, the transaction rolls back,
    and the duplicate is acked with no side effect (spec §A.6).
    """

    __tablename__ = "processed_events"
    __table_args__ = {"schema": SCHEMA}

    event_id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
