"""Add change_embeddings table for pgvector RAG pipeline

Revision ID: 003_pgvector_change_embeddings
Revises: 002_org_invites_schema
Create Date: 2026-08-23 01:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '003_pgvector_change_embeddings'
down_revision: Union[str, None] = '002_org_invites_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'change_embeddings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('org_id', sa.UUID(), nullable=False),
        sa.Column('change_id', sa.UUID(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('chunk_text', sa.Text(), nullable=False),
        sa.Column('embedding_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['change_id'], ['changes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_change_embeddings_change_id'), 'change_embeddings', ['change_id'], unique=False)
    op.create_index(op.f('ix_change_embeddings_org_id'), 'change_embeddings', ['org_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_change_embeddings_org_id'), table_name='change_embeddings')
    op.drop_index(op.f('ix_change_embeddings_change_id'), table_name='change_embeddings')
    op.drop_table('change_embeddings')
