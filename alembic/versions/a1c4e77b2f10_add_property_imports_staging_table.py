"""add property_imports staging table

Imported Excel rows are referral leads, not properties. They land here with
every sheet-absent value left NULL, instead of being forced into `properties`
with invented defaults (property_type=COMMERCIAL, price=0, lot_area=0).

Revision ID: a1c4e77b2f10
Revises: 78c157815944
Create Date: 2026-09-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1c4e77b2f10'
down_revision: Union[str, None] = '78c157815944'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'property_imports',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('address', sa.String(length=500), nullable=True),
        sa.Column('referred_by', sa.String(length=200), nullable=True),
        sa.Column('referral_type', sa.String(length=50), nullable=True),
        sa.Column('lot_area', sa.Float(), nullable=True),
        sa.Column('building_area', sa.Float(), nullable=True),
        sa.Column('lease_raw', sa.String(length=120), nullable=True),
        sa.Column('sale_raw', sa.String(length=120), nullable=True),
        sa.Column('status_hint', sa.Text(), nullable=True),
        sa.Column('sheet_name', sa.String(length=100), nullable=True),
        sa.Column('row_number', sa.Integer(), nullable=True),
        sa.Column('source_file', sa.String(length=255), nullable=True),
        sa.Column('review_status', sa.String(length=20), nullable=False, server_default='PENDING'),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('promoted_property_id', sa.Integer(), sa.ForeignKey('properties.id'), nullable=True),
        sa.Column('imported_by_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_property_imports_review_status', 'property_imports', ['review_status'])


def downgrade() -> None:
    op.drop_index('ix_property_imports_review_status', table_name='property_imports')
    op.drop_table('property_imports')
