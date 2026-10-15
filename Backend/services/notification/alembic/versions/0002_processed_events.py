"""add notification.processed_events — consumer idempotency ledger

Unlike 0001 this table is genuinely new: it was never created by raw SQL on
Supabase, so run `alembic upgrade head` normally after stamping 0001.

Why it exists: the payment service publishes payment.succeeded through an
outbox relay, which is at-least-once by design — a crash between "publish" and
"mark published" makes RabbitMQ redeliver the same event. The consumer (T16)
inserts event_id here in the same transaction as the message it writes, so a
duplicate delivery hits the primary key, the transaction rolls back, and the
event is acked with no side effect. Without it the user would see "VIP
activated" twice for a single payment.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-09
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

SCHEMA = "notification"


def upgrade() -> None:
    op.create_table(
        "processed_events",
        # Primary key *is* the dedupe mechanism — an insert conflict means
        # "already handled, ack and skip".
        sa.Column("event_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        schema=SCHEMA,
    )
    # Redelivery windows are minutes, so rows older than ~30 days can be
    # pruned; this index makes that sweep cheap.
    op.create_index(
        "processed_events_processed_at_idx",
        "processed_events",
        ["processed_at"],
        unique=False,
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_index("processed_events_processed_at_idx", table_name="processed_events", schema=SCHEMA)
    op.drop_table("processed_events", schema=SCHEMA)
