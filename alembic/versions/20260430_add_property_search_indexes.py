"""Add indexes to support server-side pagination/filtering on properties.

Revision ID: 20260430000001
Revises: 20260413000001
Create Date: 2026-04-30 00:00:00.000000

Indexes added to back common filter/sort paths used by the All Properties page:
  - created_at DESC (default sort)
  - status, property_type, transaction_status (filter facets)
  - submitted_by_id, reviewer_id (already FK-indexed in most cases, ensured here)
  - is_marked (bookmark filter)
  - pg_trgm GIN indexes on name and address for fuzzy search
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20260430000001'
down_revision: Union[str, None] = '20260413000001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_index(
        "idx_properties_created_at_desc",
        "properties",
        [sa.text("created_at DESC")],
    )
    op.create_index("idx_properties_status", "properties", ["status"])
    op.create_index("idx_properties_property_type", "properties", ["property_type"])
    op.create_index("idx_properties_transaction_status", "properties", ["transaction_status"])
    op.create_index("idx_properties_submitted_by_id", "properties", ["submitted_by_id"])
    op.create_index("idx_properties_reviewer_id", "properties", ["reviewer_id"])
    op.create_index("idx_properties_is_marked", "properties", ["is_marked"])

    op.execute(
        "CREATE INDEX idx_properties_name_trgm ON properties USING gin (name gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX idx_properties_address_trgm ON properties USING gin (address gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX idx_properties_referred_by_trgm ON properties USING gin (referred_by gin_trgm_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_properties_referred_by_trgm")
    op.execute("DROP INDEX IF EXISTS idx_properties_address_trgm")
    op.execute("DROP INDEX IF EXISTS idx_properties_name_trgm")
    op.drop_index("idx_properties_is_marked", table_name="properties")
    op.drop_index("idx_properties_reviewer_id", table_name="properties")
    op.drop_index("idx_properties_submitted_by_id", table_name="properties")
    op.drop_index("idx_properties_transaction_status", table_name="properties")
    op.drop_index("idx_properties_property_type", table_name="properties")
    op.drop_index("idx_properties_status", table_name="properties")
    op.drop_index("idx_properties_created_at_desc", table_name="properties")
