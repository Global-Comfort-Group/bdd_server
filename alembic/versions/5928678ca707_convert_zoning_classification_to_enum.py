"""convert_zoning_classification_to_enum

Revision ID: 5928678ca707
Revises: 20251008_update_status
Create Date: 2025-10-08 10:39:01.654502

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5928678ca707'
down_revision: Union[str, None] = '20251008_update_status'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the enum type
    zoning_classification_enum = sa.Enum(
        'Residential',
        'Commercial', 
        'Agricultural',
        'Agricultural - Beach Front',
        'Industrial',
        name='zoningclassification'
    )
    zoning_classification_enum.create(op.get_bind(), checkfirst=True)
    
    # Update the column to use the enum type
    # Using USING clause to convert existing string values to enum
    op.execute("""
        ALTER TABLE properties 
        ALTER COLUMN zoning_classification 
        TYPE zoningclassification 
        USING zoning_classification::zoningclassification
    """)


def downgrade() -> None:
    # Convert back to varchar
    op.execute("""
        ALTER TABLE properties 
        ALTER COLUMN zoning_classification 
        TYPE VARCHAR(100)
        USING zoning_classification::text
    """)
    
    # Drop the enum type
    op.execute("DROP TYPE IF EXISTS zoningclassification")
