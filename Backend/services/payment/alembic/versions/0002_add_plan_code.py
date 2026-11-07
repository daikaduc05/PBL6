"""add plan_code to payment.transactions

T29: records which VIP plan was purchased, so T31's event publish can look
up its duration_days later (there's still no `plans` table — see
payment.plans.PLANS for the hardcoded catalogue). Unlike 0001, this one
is genuinely new — run `alembic upgrade head`, not `stamp head`.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-15
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "transactions",
        sa.Column("plan_code", sa.Text(), nullable=False, server_default="VIP_1_MONTH"),
        schema="payment",
    )


def downgrade() -> None:
    op.drop_column("transactions", "plan_code", schema="payment")
