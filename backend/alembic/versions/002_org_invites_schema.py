"""Add org_invites table

Revision ID: 002_org_invites_schema
Revises: 001_initial_schema
Create Date: 2026-08-23 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '002_org_invites_schema'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'org_invites',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('org_id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('admin', 'engineer', 'business_ops', 'viewer', name='userrole'), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_org_invites_email'), 'org_invites', ['email'], unique=False)
    op.create_index(op.f('ix_org_invites_org_id'), 'org_invites', ['org_id'], unique=False)
    op.create_index(op.f('ix_org_invites_token'), 'org_invites', ['token'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_org_invites_token'), table_name='org_invites')
    op.drop_index(op.f('ix_org_invites_org_id'), table_name='org_invites')
    op.drop_index(op.f('ix_org_invites_email'), table_name='org_invites')
    op.drop_table('org_invites')
