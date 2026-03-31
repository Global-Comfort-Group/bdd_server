"""Add building_area, floors, parking_slots, rooms to properties

Revision ID: 20260331000001
Revises: 20260325000001
Create Date: 2026-03-31 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20260331000001'
down_revision: Union[str, None] = '20260325000001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('properties', sa.Column('building_area', sa.Float(), nullable=True))
    op.add_column('properties', sa.Column('floors', sa.Integer(), nullable=True))
    op.add_column('properties', sa.Column('parking_slots', sa.Integer(), nullable=True))
    op.add_column('properties', sa.Column('rooms', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('properties', 'rooms')
    op.drop_column('properties', 'parking_slots')
    op.drop_column('properties', 'floors')
    op.drop_column('properties', 'building_area')
