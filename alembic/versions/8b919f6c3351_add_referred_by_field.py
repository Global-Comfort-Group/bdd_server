"""add_referred_by_field

Revision ID: 8b919f6c3351
Revises: c501c306edc1
Create Date: 2025-10-08 11:11:53.515426

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8b919f6c3351'
down_revision: Union[str, None] = 'c501c306edc1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add referred_by column for tracking property referrals
    op.add_column('properties', 
        sa.Column('referred_by', sa.String(length=200), nullable=True)
    )


def downgrade() -> None:
    # Remove referred_by column
    op.drop_column('properties', 'referred_by')
