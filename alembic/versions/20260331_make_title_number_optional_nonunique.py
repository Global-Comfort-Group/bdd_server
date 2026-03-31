"""Make title_number optional and non-unique

Revision ID: 20260331000002
Revises: 20260331000001
Create Date: 2026-03-31 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20260331000002'
down_revision: Union[str, None] = '20260331000001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the unique constraint and index on title_number
    op.drop_index('ix_properties_title_number', table_name='properties', if_exists=True)
    op.alter_column('properties', 'title_number',
                    existing_type=sa.String(100),
                    nullable=True)


def downgrade() -> None:
    op.alter_column('properties', 'title_number',
                    existing_type=sa.String(100),
                    nullable=False)
    op.create_index('ix_properties_title_number', 'properties', ['title_number'], unique=True)
