"""add property_import_tokens

The import preview/confirm handover kept parsed rows in an in-process dict.
The app runs `uvicorn --workers 2`, so confirm frequently landed on a worker
that had never seen the token, and a redeploy between the two calls lost it
outright — surfacing as "Import token not found or expired". The rows are now
persisted here.

Revision ID: c9f2a83b6e17
Revises: b7d3e91a4c25
Create Date: 2026-09-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'c9f2a83b6e17'
down_revision: Union[str, None] = 'b7d3e91a4c25'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'property_import_tokens',
        sa.Column('token', sa.String(length=36), primary_key=True),
        sa.Column('rows', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('source_file', sa.String(length=255), nullable=True),
        sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_property_import_tokens_expires_at', 'property_import_tokens', ['expires_at'])


def downgrade() -> None:
    op.drop_index('ix_property_import_tokens_expires_at', table_name='property_import_tokens')
    op.drop_table('property_import_tokens')
