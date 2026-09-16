"""baseline: account.users

Mirrors Backend/db/01_account.sql exactly. That file already created this
table directly on Supabase (this project started on raw SQL before Alembic
was wired up), so on the existing environment run `alembic stamp head`
instead of `upgrade head` — do NOT run upgrade against it, it would try to
create a table that already exists. A genuinely fresh database (e.g. a
future CI test database) uses `upgrade head` normally.

Revision ID: 0001
Revises:
Create Date: 2026-09-16
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
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("email", sa.Text(), nullable=False, unique=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("full_name", sa.Text(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False, server_default="CUSTOMER"),
        sa.Column("status", sa.Text(), nullable=False, server_default="ACTIVE"),
        sa.Column("is_vip", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("vip_expired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("role IN ('CUSTOMER', 'EDITOR', 'ADMIN')", name="users_role_check"),
        sa.CheckConstraint("status IN ('ACTIVE', 'INACTIVE', 'LOCKED')", name="users_status_check"),
        schema="account",
    )


def downgrade() -> None:
    op.drop_table("users", schema="account")
