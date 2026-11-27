"""add content.outbox

Revision ID: e8b1c4a92f01
Revises: daa28468fddd
Create Date: 2026-11-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "e8b1c4a92f01"
down_revision: str | Sequence[str] | None = "daa28468fddd"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


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
        schema="content",
    )
    op.create_index(
        "content_outbox_unpublished_idx",
        "outbox",
        ["created_at"],
        schema="content",
        postgresql_where=sa.text("published_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("content_outbox_unpublished_idx", table_name="outbox", schema="content")
    op.drop_table("outbox", schema="content")

