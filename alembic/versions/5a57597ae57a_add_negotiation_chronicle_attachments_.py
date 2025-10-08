"""add_negotiation_chronicle_attachments_table

Revision ID: 5a57597ae57a
Revises: e38a28be0e92
Create Date: 2025-10-01 17:32:57.376578

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5a57597ae57a'
down_revision: Union[str, None] = 'e38a28be0e92'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create negotiation_chronicle_attachments table
    op.create_table(
        'negotiation_chronicle_attachments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nego_table_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_url', sa.String(length=500), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('parsed_data', sa.JSON(), nullable=False),
        sa.Column('uploaded_by', sa.Integer(), nullable=False),
        sa.Column('upload_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['nego_table_id'], ['nego_tables.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_negotiation_chronicle_attachments_id'), 'negotiation_chronicle_attachments', ['id'], unique=False)


def downgrade() -> None:
    # Drop negotiation_chronicle_attachments table
    op.drop_index(op.f('ix_negotiation_chronicle_attachments_id'), table_name='negotiation_chronicle_attachments')
    op.drop_table('negotiation_chronicle_attachments')
