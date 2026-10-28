"""add payment.outbox

T31: outbox pattern — a row here is written in the same DB transaction as
a `transactions` status update, and the relay worker
(payment.outbox.relay) publishes unpublished rows to RabbitMQ. Reintroduces
the `outbox` table backend.md §5 originally specified (dropped from the
simplified ER diagram until actually needed — see 04_payment.sql).

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-15
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "outbox",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("aggregate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        schema="payment",
    )
    op.create_index(
        "outbox_unpublished_idx",
        "outbox",
        ["created_at"],
        schema="payment",
        postgresql_where=sa.text("published_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("outbox_unpublished_idx", table_name="outbox", schema="payment")
    op.drop_table("outbox", schema="payment")
