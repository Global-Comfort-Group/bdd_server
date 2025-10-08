"""convert_zoning_classification_to_varchar

Revision ID: 48f4018b5e86
Revises: 3e1d4dd87c16
Create Date: 2025-10-08 12:33:12.882882

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '48f4018b5e86'
down_revision: Union[str, None] = '3e1d4dd87c16'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert zoning_classification from enum to varchar
    op.execute("""
        ALTER TABLE properties 
        ALTER COLUMN zoning_classification 
        TYPE VARCHAR(100)
        USING zoning_classification::text
    """)
    
    # Drop the enum type
    op.execute("DROP TYPE IF EXISTS zoningclassification")


def downgrade() -> None:
    # Recreate the enum type
    zoning_classification_enum = sa.Enum(
        'Residential',
        'Commercial', 
        'Agricultural',
        'Agricultural - Beach Front',
        'Industrial',
        name='zoningclassification'
    )
    zoning_classification_enum.create(op.get_bind(), checkfirst=True)
    
    # Convert back to enum
    op.execute("""
        ALTER TABLE properties 
        ALTER COLUMN zoning_classification 
        TYPE zoningclassification 
        USING zoning_classification::zoningclassification
    """)
