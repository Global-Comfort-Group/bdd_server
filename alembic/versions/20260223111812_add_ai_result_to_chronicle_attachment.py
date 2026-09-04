"""add ai_result to negotiation_chronicle_attachments

Revision ID: 20260223111812
Revises: f41df5d9d8a2
Create Date: 2026-02-23 11:18:12.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260223111812'
down_revision = 'f41df5d9d8a2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'negotiation_chronicle_attachments',
        sa.Column('ai_result', sa.JSON(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('negotiation_chronicle_attachments', 'ai_result')
