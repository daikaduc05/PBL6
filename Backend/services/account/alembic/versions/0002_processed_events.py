"""add account.processed_events — payment.succeeded consumer idempotency ledger

Genuinely new — never existed on raw SQL, so run `alembic upgrade head`
normally (unlike 0001, which only stamps an already-existing table).

Why: payment's outbox relay (T31) is at-least-once — a crash between
"publish" and "mark published" makes RabbitMQ redeliver the same
payment.succeeded event. T26's consumer inserts event_id here in the same
transaction as the VIP upgrade it applies, so a duplicate delivery hits
the primary key, the transaction rolls back, and the event is acked with
no side effect. Same pattern as notification service's own
processed_events table (notification/alembic/versions/0002).

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-15
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

SCHEMA = "account"


def upgrade() -> None:
    op.create_table(
        "processed_events",
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
