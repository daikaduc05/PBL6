"""add notification.messages.type — what produced each notification

Until now every row was a study reminder, so the kind of a notification could
be inferred from its title. T16 starts writing five more kinds into the same
table and that inference stops working: the title is display copy, and any
reword silently breaks every rule keyed on its text.

Timing is the whole point of doing this before T16 rather than after. Right
now the backfill below is a single unconditional UPDATE that cannot be wrong,
because only one kind exists. Once the consumer has run, the only way to label
old rows is to guess from title strings — including rows written under titles
that were since edited, which no amount of care can recover.

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-07
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

SCHEMA = "notification"

# Mirrors notification.models.message.MessageType, which in turn mirrors the
# routing keys in backend.md §6.
TYPES = (
    "STUDY_REMINDER",
    "PAYMENT_SUCCEEDED",
    "VIP_EXPIRED",
    "ACCOUNT_LOCKED",
    "ACCOUNT_UNLOCKED",
    "LESSON_PUBLISHED",
)


def upgrade() -> None:
    # Three steps rather than one column with a server_default: a default of
    # STUDY_REMINDER would also quietly label every future row that forgets to
    # pass a type, which is precisely the silent-wrongness this column exists
    # to remove. Adding it nullable, filling it, then demanding NOT NULL
    # leaves no way to insert an unlabelled row afterwards.
    op.add_column("messages", sa.Column("type", sa.Text(), nullable=True), schema=SCHEMA)

    op.execute(f"update {SCHEMA}.messages set type = 'STUDY_REMINDER'")  # noqa: S608

    op.alter_column("messages", "type", nullable=False, schema=SCHEMA)

    values = ", ".join(f"'{t}'" for t in TYPES)
    op.create_check_constraint(
        "messages_type_check", "messages", f"type in ({values})", schema=SCHEMA
    )

    op.create_index(
        "messages_user_type_idx",
        "messages",
        ["user_id", "type", sa.text("created_at DESC")],
        unique=False,
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_index("messages_user_type_idx", table_name="messages", schema=SCHEMA)
    op.drop_constraint("messages_type_check", "messages", schema=SCHEMA)
    op.drop_column("messages", "type", schema=SCHEMA)
