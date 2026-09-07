"""Widen place_id column from VARCHAR(255) to TEXT

Google Maps Place IDs can exceed 255 characters, causing property submission failures.

Revision ID: 20260413000001
Revises: 20260331000002
Create Date: 2026-04-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20260413000001'
down_revision: Union[str, None] = '20260331000002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('properties', 'place_id',
                    existing_type=sa.VARCHAR(length=255),
                    type_=sa.Text(),
                    existing_nullable=True)


def downgrade() -> None:
    op.alter_column('properties', 'place_id',
                    existing_type=sa.Text(),
                    type_=sa.VARCHAR(length=255),
                    existing_nullable=True)
