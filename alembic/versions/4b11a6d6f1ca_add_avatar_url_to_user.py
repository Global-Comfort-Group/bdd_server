"""add_avatar_url_to_user

Revision ID: 4b11a6d6f1ca
Revises: 20251003_170757
Create Date: 2025-10-07 12:29:20.250657

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4b11a6d6f1ca'
down_revision: Union[str, None] = '20251003_170757'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add avatar_url column to user table
    op.add_column('user', sa.Column('avatar_url', sa.String(length=500), nullable=True))


def downgrade() -> None:
    # Remove avatar_url column from user table
    op.drop_column('user', 'avatar_url')
