"""add analysis_status, analyzed_at, analysis_error, file_sha256 to chronicle attachments

Revision ID: 20260504000001
Revises: 20260430000001
Create Date: 2026-05-04 00:00:00.000000

Decouples upload from Gemini analysis. Existing rows are backfilled to COMPLETED
when ai_result is non-null (analysis already ran), otherwise PENDING.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20260504000001'
down_revision: Union[str, None] = '20260430000001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'negotiation_chronicle_attachments',
        sa.Column(
            'analysis_status',
            sa.String(20),
            nullable=False,
            server_default='PENDING',
        ),
    )
    op.add_column(
        'negotiation_chronicle_attachments',
        sa.Column('analyzed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        'negotiation_chronicle_attachments',
        sa.Column('analysis_error', sa.Text(), nullable=True),
    )
    op.add_column(
        'negotiation_chronicle_attachments',
        sa.Column('file_sha256', sa.String(64), nullable=True),
    )

    op.execute(
        """
        UPDATE negotiation_chronicle_attachments
        SET analysis_status = 'COMPLETED',
            analyzed_at = COALESCE(updated_at, created_at)
        WHERE ai_result IS NOT NULL
        """
    )

    op.create_index(
        'idx_chronicle_attachments_analysis_status',
        'negotiation_chronicle_attachments',
        ['analysis_status'],
    )
    op.create_index(
        'idx_chronicle_attachments_file_sha256',
        'negotiation_chronicle_attachments',
        ['file_sha256'],
    )


def downgrade() -> None:
    op.drop_index(
        'idx_chronicle_attachments_file_sha256',
        table_name='negotiation_chronicle_attachments',
    )
    op.drop_index(
        'idx_chronicle_attachments_analysis_status',
        table_name='negotiation_chronicle_attachments',
    )
    op.drop_column('negotiation_chronicle_attachments', 'file_sha256')
    op.drop_column('negotiation_chronicle_attachments', 'analysis_error')
    op.drop_column('negotiation_chronicle_attachments', 'analyzed_at')
    op.drop_column('negotiation_chronicle_attachments', 'analysis_status')
