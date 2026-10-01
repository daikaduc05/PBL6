"""baseline: payment.transactions

Mirrors Backend/db/04_payment.sql exactly. That file already created this
table directly on Supabase, so on the existing environment run
`alembic stamp head` instead of `upgrade head` — do NOT run upgrade against
it, it would try to create a table that already exists. A genuinely fresh
database (e.g. a future CI test database) uses `upgrade head` normally.

Revision ID: 0001
Revises:
Create Date: 2026-10-01
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "transactions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("payment_method", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="PENDING"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("amount >= 0", name="transactions_amount_check"),
        sa.CheckConstraint(
            "payment_method IN ('VNPAY', 'MOMO')", name="transactions_payment_method_check"
        ),
        sa.CheckConstraint(
            "status IN ('PENDING', 'SUCCESS', 'FAILED')", name="transactions_status_check"
        ),
        schema="payment",
    )


def downgrade() -> None:
    op.drop_table("transactions", schema="payment")
