"""add_is_marked_field_for_bookmark

Revision ID: 3e1d4dd87c16
Revises: 8b919f6c3351
Create Date: 2025-10-08 11:31:20.819524

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3e1d4dd87c16'
down_revision: Union[str, None] = '8b919f6c3351'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_marked column for bookmark/flag functionality
    op.add_column('properties', 
        sa.Column('is_marked', sa.Boolean(), nullable=False, server_default='false')
    )


def downgrade() -> None:
    # Remove is_marked column
    op.drop_column('properties', 'is_marked')
