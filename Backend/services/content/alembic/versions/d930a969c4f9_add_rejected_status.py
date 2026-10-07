"""add rejected status

Revision ID: d930a969c4f9
Revises: 6d4b504b9200
Create Date: 2026-10-07 11:35:27.718282

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd930a969c4f9'
down_revision: Union[str, Sequence[str], None] = '6d4b504b9200'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE content.lesson_status_enum ADD VALUE IF NOT EXISTS 'rejected'")


def downgrade() -> None:
    """Downgrade schema."""
    # Postgres doesn't support DROP VALUE for enums easily. We leave it as is or delete the usage.
    pass
