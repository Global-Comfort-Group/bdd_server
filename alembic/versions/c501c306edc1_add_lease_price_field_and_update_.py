"""add_lease_price_field_and_update_transaction_status

Revision ID: c501c306edc1
Revises: 5928678ca707
Create Date: 2025-10-08 10:59:08.983651

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c501c306edc1'
down_revision: Union[str, None] = '5928678ca707'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add lease_price column for Sale & Lease transactions
    op.add_column('properties', 
        sa.Column('lease_price', sa.Numeric(precision=15, scale=2), nullable=True)
    )


def downgrade() -> None:
    # Remove lease_price column
    op.drop_column('properties', 'lease_price')
