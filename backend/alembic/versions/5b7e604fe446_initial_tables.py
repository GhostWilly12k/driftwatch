"""initial tables

Revision ID: 5b7e604fe446
Revises: 
Create Date: 2026-07-07 03:51:47.952923

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '5b7e604fe446'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('users',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('plan', sa.String(), nullable=True),
    sa.Column('avatar_url', sa.String(), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('trades',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=True),
    sa.Column('symbol', sa.String(), nullable=False),
    sa.Column('direction', sa.String(), nullable=False),
    sa.Column('strategy', sa.String(), nullable=True),
    sa.Column('entry_price', sa.Numeric(), nullable=True),
    sa.Column('exit_price', sa.Numeric(), nullable=True),
    sa.Column('stop_loss', sa.Numeric(), nullable=True),
    sa.Column('profit_target', sa.Numeric(), nullable=True),
    sa.Column('planned_entry', sa.Numeric(), nullable=True),
    sa.Column('planned_stop', sa.Numeric(), nullable=True),
    sa.Column('quantity', sa.Numeric(), nullable=True),
    sa.Column('r_result', sa.Numeric(), nullable=True),
    sa.Column('mae', sa.Numeric(), nullable=True),
    sa.Column('mfe', sa.Numeric(), nullable=True),
    sa.Column('mindset', sa.String(), nullable=True),
    sa.Column('emotion_pre', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('confidence', sa.Integer(), nullable=True),
    sa.Column('rationale', sa.String(), nullable=True),
    sa.Column('post_notes', sa.String(), nullable=True),
    sa.Column('chart_url', sa.String(), nullable=True),
    sa.Column('psychology_tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('rule_breaks', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('entered_at', sa.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('exited_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', 'entered_at'),
    postgresql_partition_by='RANGE (entered_at)'
    )
    op.create_table('user_settings',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('account_size', sa.Numeric(), nullable=True),
    sa.Column('risk_per_trade', sa.Numeric(), nullable=True),
    sa.Column('daily_max_loss', sa.Numeric(), nullable=True),
    sa.Column('weekly_max_loss', sa.Numeric(), nullable=True),
    sa.Column('theme', sa.String(), nullable=True),
    sa.Column('agent_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('notif_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id')
    )

    op.execute("""
        SELECT extensions.create_parent(
            p_parent_table => 'public.trades',
            p_control       => 'entered_at',
            p_interval      => '1 month',
            p_premake       => 3
        );
    """)

    op.execute("""
        SELECT cron.schedule('partman-maintenance', '@daily', $$CALL extensions.run_maintenance_proc()$$);
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("SELECT cron.unschedule('partman-maintenance');")
    op.execute("SELECT extensions.undo_partition('public.trades', p_keep_table => false);")
    op.drop_table('user_settings')
    op.drop_table('trades')
    op.drop_table('users')