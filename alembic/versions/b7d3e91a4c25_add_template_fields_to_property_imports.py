"""add template fields to property_imports

The "TEMPLATE (Complete)" sheet supplies the fields the monthly sheets lack —
price, property type, zoning, transaction, title, floors, rooms, parking. Rows
imported from it can be promoted with nothing left to fill in. All nullable:
a monthly sheet has no such columns and leaves them NULL.

Revision ID: b7d3e91a4c25
Revises: a1c4e77b2f10
Create Date: 2026-09-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b7d3e91a4c25'
down_revision: Union[str, None] = 'a1c4e77b2f10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_COLUMNS = [
    ('price', sa.Numeric(15, 2)),
    ('lease_price', sa.Numeric(15, 2)),
    ('property_type', sa.String(length=50)),
    ('zoning_classification', sa.String(length=100)),
    ('transaction_status', sa.String(length=10)),
    ('title_number', sa.String(length=100)),
    ('floors', sa.Integer()),
    ('rooms', sa.Integer()),
    ('parking_slots', sa.Integer()),
    ('description', sa.Text()),
]


def upgrade() -> None:
    for name, type_ in _COLUMNS:
        op.add_column('property_imports', sa.Column(name, type_, nullable=True))


def downgrade() -> None:
    for name, _ in reversed(_COLUMNS):
        op.drop_column('property_imports', name)
