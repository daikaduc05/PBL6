"""Maps 1:1 onto account.users, created by Backend/db/01_account.sql.
Alembic's baseline migration (alembic/versions/) mirrors this table — the
two must be kept in sync by hand since the live table predates Alembic here.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pbl6_common.db import Base
from sqlalchemy import Boolean, CheckConstraint, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

ROLES = ("CUSTOMER", "EDITOR", "ADMIN")
STATUSES = ("ACTIVE", "INACTIVE", "LOCKED")


def _sql_in_list(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{v}'" for v in values)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(f"role IN ({_sql_in_list(ROLES)})", name="users_role_check"),
        CheckConstraint(f"status IN ({_sql_in_list(STATUSES)})", name="users_status_check"),
        {"schema": "account"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False, default="CUSTOMER")
    status: Mapped[str] = mapped_column(String, nullable=False, default="ACTIVE")
    is_vip: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    vip_expired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
