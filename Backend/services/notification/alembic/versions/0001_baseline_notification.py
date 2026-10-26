"""baseline: notification.messages + notification.settings

Mirrors Backend/db/05_notification.sql exactly. That file already created both
tables directly on Supabase (this project started on raw SQL before Alembic was
wired up), so on the existing environment run `alembic stamp 0001` instead of
`upgrade head` — do NOT run upgrade against it, it would try to create tables
that already exist. A genuinely fresh database (CI, a local container) uses
`upgrade head` normally.

Revision ID: 0001
Revises:
Create Date: 2026-10-09
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

SCHEMA = "notification"


def upgrade() -> None:
    # 00_schemas.sql creates this on Supabase; repeated here so a fresh
    # database (CI) can run `upgrade head` without the raw SQL files.
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "messages",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # Logical FK to account.users.id — no constraint crosses a schema.
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        schema=SCHEMA,
    )
    # Partial index: the unread badge and the unread_only filter only ever look
    # at unread rows, so the read ones do not belong in the index.
    op.create_index(
        "messages_user_unread_idx",
        "messages",
        ["user_id", sa.text("created_at DESC")],
        unique=False,
        schema=SCHEMA,
        postgresql_where=sa.text("is_read = false"),
    )

    op.create_table(
        "settings",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "enable_daily_reminder",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("device_token", sa.Text(), nullable=True),
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_table("settings", schema=SCHEMA)
    op.drop_index("messages_user_unread_idx", table_name="messages", schema=SCHEMA)
    op.drop_table("messages", schema=SCHEMA)
