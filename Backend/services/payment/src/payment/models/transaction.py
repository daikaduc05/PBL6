"""Maps 1:1 onto payment.transactions, created by Backend/db/04_payment.sql.
Alembic's baseline migration (alembic/versions/) mirrors this table — the
two must be kept in sync by hand since the live table predates Alembic here
(same situation as account.models.user — see that file's docstring).

Simplified per the ER diagram the team settled on: no `plans` table (price
is just the raw amount per transaction) and no `outbox` table — T31 adds
that when it's actually needed.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pbl6_common.db import Base
from sqlalchemy import CheckConstraint, DateTime, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

PAYMENT_METHODS = ("VNPAY", "MOMO")
STATUSES = ("PENDING", "SUCCESS", "FAILED")


def _sql_in_list(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{v}'" for v in values)


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="transactions_amount_check"),
        CheckConstraint(
            f"payment_method IN ({_sql_in_list(PAYMENT_METHODS)})",
            name="transactions_payment_method_check",
        ),
        CheckConstraint(f"status IN ({_sql_in_list(STATUSES)})", name="transactions_status_check"),
        {"schema": "payment"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    # Logical FK -> account.users.id — no cross-schema foreign key, per
    # backend.md's bounded-context rule.
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    payment_method: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="PENDING")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
