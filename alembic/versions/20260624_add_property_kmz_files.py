"""add property_kmz_files table

Revision ID: 20260624000001
Revises: 20260504000001
Create Date: 2026-06-24 00:00:00.000000

Stores per-property KMZ (Google Earth) uploads plus the GeoJSON FeatureCollection
parsed from each. One property may have many KMZ files.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20260624000001'
down_revision: Union[str, None] = '20260504000001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'property_kmz_files',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('property_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('oss_object_key', sa.String(length=500), nullable=False),
        sa.Column('file_url', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('file_sha256', sa.String(length=64), nullable=True),
        sa.Column('parsed_data', sa.JSON(), nullable=False),
        sa.Column('feature_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('uploaded_by', sa.Integer(), nullable=True),
        sa.Column('upload_date', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ),
        sa.ForeignKeyConstraint(['uploaded_by'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_property_kmz_property_id', 'property_kmz_files', ['property_id'])
    op.create_index('idx_property_kmz_file_sha256', 'property_kmz_files', ['file_sha256'])


def downgrade() -> None:
    op.drop_index('idx_property_kmz_file_sha256', table_name='property_kmz_files')
    op.drop_index('idx_property_kmz_property_id', table_name='property_kmz_files')
    op.drop_table('property_kmz_files')
