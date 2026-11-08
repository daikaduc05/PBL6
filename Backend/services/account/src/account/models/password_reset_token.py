"""Password-reset tokens. Only the SHA-256 hash is ever stored — the raw
token only exists in the email link, exactly the same principle as
refresh-token `jti` revocation (pbl6_common.security). A token is valid
once: `used_at` is set the moment it's redeemed, so replaying an old
reset link (e.g. from an email the user forwarded) always fails.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pbl6_common.db import Base
from sqlalchemy import DateTime, Index, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    __table_args__ = (
        Index("password_reset_tokens_user_id_idx", "user_id"),
        {"schema": "account"},
    )

    token_hash: Mapped[str] = mapped_column(Text, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
