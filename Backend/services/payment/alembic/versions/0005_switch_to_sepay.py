"""payment.transactions.payment_method: VNPAY/MOMO -> SEPAY only

VNPay's merchant account hit a dead end (old merchantv2 login doesn't
carry over to their new "VNPAY ID" unified login) and Momo's sandbox
requires a real registered business account — see T29's commit for the
full dead-end chain. Both were only ever reachable via MOCK_PAYMENT=true.

SePay (a Vietnamese bank-transfer monitoring service) needs none of
that: just a personal bank account + an API/webhook secret, which the
project owner already has. So this isn't "add a third option" — it
replaces VNPAY/MOMO outright, since neither ever had working credentials
to begin with.

Deletes the handful of VNPAY/MOMO rows created during T29/T30/T31's
mock-mode testing (never real payments — this is a dev database) before
narrowing the CHECK constraint, since Postgres validates a new CHECK
against every existing row.

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-25
"""

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

SCHEMA = "payment"


def upgrade() -> None:
    op.execute(
        sa.text("delete from payment.transactions where payment_method in ('VNPAY', 'MOMO')")
    )
    op.drop_constraint("transactions_payment_method_check", "transactions", schema=SCHEMA)
    op.create_check_constraint(
        "transactions_payment_method_check",
        "transactions",
        "payment_method IN ('SEPAY')",
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_constraint("transactions_payment_method_check", "transactions", schema=SCHEMA)
    op.create_check_constraint(
        "transactions_payment_method_check",
        "transactions",
        "payment_method IN ('VNPAY', 'MOMO')",
        schema=SCHEMA,
    )
