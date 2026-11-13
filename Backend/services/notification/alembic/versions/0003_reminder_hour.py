"""add notification.settings.reminder_hour — per-user reminder time

Function 8.1 originally fired one cron at 20:00 for everybody. Letting each
learner pick their own hour means the job now runs hourly and selects whoever
asked for the hour that just started.

Default 20 keeps existing rows behaving exactly as before.

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

SCHEMA = "notification"


def upgrade() -> None:
    op.add_column(
        "settings",
        sa.Column(
            "reminder_hour",
            sa.SmallInteger(),
            nullable=False,
            server_default=sa.text("20"),
        ),
        schema=SCHEMA,
    )
    # The API validates this too, but the constraint is what guarantees no
    # process can ever write an hour the scheduler cannot match.
    op.create_check_constraint(
        "settings_reminder_hour_check",
        "settings",
        "reminder_hour >= 0 AND reminder_hour <= 23",
        schema=SCHEMA,
    )
    # The hourly job asks "who wants a reminder at hour H and has it enabled",
    # so index exactly that pair.
    op.create_index(
        "settings_reminder_hour_idx",
        "settings",
        ["reminder_hour"],
        unique=False,
        schema=SCHEMA,
        postgresql_where=sa.text("enable_daily_reminder = true"),
    )


def downgrade() -> None:
    op.drop_index("settings_reminder_hour_idx", table_name="settings", schema=SCHEMA)
    op.drop_constraint("settings_reminder_hour_check", "settings", schema=SCHEMA)
    op.drop_column("settings", "reminder_hour", schema=SCHEMA)
