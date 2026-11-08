"""add account.password_reset_tokens

Genuinely new — run `alembic upgrade head` normally.

Only the SHA-256 hash of a reset token is ever stored (token_hash is the
primary key); the raw token exists only in the emailed link. `used_at`
makes a token single-use — set the moment it's redeemed.

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-28
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

SCHEMA = "account"


def upgrade() -> None:
    op.create_table(
        "password_reset_tokens",
        sa.Column("token_hash", sa.Text(), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        schema=SCHEMA,
    )
    op.create_index(
        "password_reset_tokens_user_id_idx",
        "password_reset_tokens",
        ["user_id"],
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_index(
        "password_reset_tokens_user_id_idx", table_name="password_reset_tokens", schema=SCHEMA
    )
    op.drop_table("password_reset_tokens", schema=SCHEMA)
