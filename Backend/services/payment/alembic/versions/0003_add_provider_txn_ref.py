"""add provider_txn_ref to payment.transactions

T30: records the gateway's own transaction id (vnp_TransactionNo / MoMo
transId) the first time a webhook is processed, so a redelivered webhook
is a no-op instead of double-applying (backend.md §12: "idempotent on
provider_txn_ref"). Genuinely new — run `alembic upgrade head`.

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-15
"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "transactions",
        sa.Column("provider_txn_ref", sa.Text(), nullable=True),
        schema="payment",
    )
    op.create_unique_constraint(
        "transactions_provider_txn_ref_key",
        "transactions",
        ["provider_txn_ref"],
        schema="payment",
    )


def downgrade() -> None:
    op.drop_constraint(
        "transactions_provider_txn_ref_key", "transactions", schema="payment", type_="unique"
    )
    op.drop_column("transactions", "provider_txn_ref", schema="payment")
