"""add password_hash to users

Revision ID: 8f2a1c9d4b6e
Revises: 5b7e604fe446
Create Date: 2026-07-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '8f2a1c9d4b6e'
down_revision: Union[str, Sequence[str], None] = '5b7e604fe446'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # nullable=True first so the column can land on a table that may already
    # have rows, then backfill (none expected pre-Sprint-1) and tighten to
    # NOT NULL. Safe on an empty users table too.
    op.add_column('users', sa.Column('password_hash', sa.String(), nullable=True))
    op.execute("UPDATE users SET password_hash = '' WHERE password_hash IS NULL")
    op.alter_column('users', 'password_hash', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'password_hash')