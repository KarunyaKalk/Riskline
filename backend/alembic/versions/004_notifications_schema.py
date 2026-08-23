"""Add notifications and notification_preferences tables

Revision ID: 004_notifications_schema
Revises: 003_pgvector_change_embeddings
Create Date: 2026-08-23 02:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '004_notifications_schema'
down_revision: Union[str, None] = '003_pgvector_change_embeddings'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'notifications',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('org_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False, server_default='high_risk_alert'),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('target_url', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_org_id'), 'notifications', ['org_id'], unique=False)
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)

    op.create_table(
        'notification_preferences',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('inapp_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('email_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('slack_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('min_risk_level', sa.String(length=50), nullable=False, server_default='high'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_preferences_user_id'), 'notification_preferences', ['user_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_notification_preferences_user_id'), table_name='notification_preferences')
    op.drop_table('notification_preferences')
    op.drop_index(op.f('ix_notifications_user_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_org_id'), table_name='notifications')
    op.drop_table('notifications')
