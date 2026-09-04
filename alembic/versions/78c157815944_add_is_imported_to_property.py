"""add_is_imported_to_property

Revision ID: 78c157815944
Revises: 20260624000001
Create Date: 2026-09-02 15:26:54.625149

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '78c157815944'
down_revision: Union[str, None] = '20260624000001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('properties', sa.Column('is_imported', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('properties', 'is_imported')
