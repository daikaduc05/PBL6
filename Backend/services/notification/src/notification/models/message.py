"""Maps 1:1 onto notification.messages, created by Backend/db/05_notification.sql.

Alembic's baseline migration mirrors this table — the live table predates
Alembic here, so the two are kept in sync by hand (same arrangement as
account.users).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pbl6_common.db import Base
from sqlalchemy import Boolean, DateTime, Index, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        Index(
            "messages_user_unread_idx",
            "user_id",
            text("created_at DESC"),
            postgresql_where=text("is_read = false"),
        ),
        {"schema": "notification"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    # Logical FK to account.users.id — no constraint crosses a schema boundary.
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
