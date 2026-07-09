"""Add document_type to property_attachments

Revision ID: 20260325000001
Revises: 20260223111812
Create Date: 2026-03-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '20260325000001'
down_revision: Union[str, None] = '48f4018b5e86'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'property_attachments',
        sa.Column('document_type', sa.String(50), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('property_attachments', 'document_type')
