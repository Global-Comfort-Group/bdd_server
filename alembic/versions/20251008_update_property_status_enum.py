"""Update property status enum values

Revision ID: 20251008_update_status
Revises: f3950a9ad6f4
Create Date: 2025-10-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20251008_update_status'
down_revision: Union[str, None] = 'f3950a9ad6f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create new enum type with updated values
    new_status_enum = postgresql.ENUM(
        'PROPERTY_SOURCING',
        'PROPERTY_SCREENING_FUNG_SHUI',
        'PBY_STUDY',
        'EXECOM',
        'BOARD_APPROVAL',
        'DUE_DILIGENCE',
        'NEGOTIATION',
        'COL_DOAS_SIGNING',
        name='new_propertystatus'
    )
    new_status_enum.create(op.get_bind())
    
    # Add temporary column with new enum
    op.add_column('properties', sa.Column('status_new', new_status_enum, nullable=True))
    
    # Migrate existing data with updated status values
    op.execute("""
        UPDATE properties 
        SET status_new = CASE status::text
            WHEN 'PROPERTY_SOURCING' THEN 'PROPERTY_SOURCING'::new_propertystatus
            WHEN 'PROPERTY_STUDY' THEN 'PROPERTY_SCREENING_FUNG_SHUI'::new_propertystatus
            WHEN 'PBY_PREPARATION' THEN 'PBY_STUDY'::new_propertystatus
            WHEN 'COUNCIL_APPROVAL' THEN 'EXECOM'::new_propertystatus
            WHEN 'NEGOTIATION' THEN 'NEGOTIATION'::new_propertystatus
            WHEN 'DUE_DILIGENCE' THEN 'DUE_DILIGENCE'::new_propertystatus
            WHEN 'CONTRACT_SIGNING' THEN 'COL_DOAS_SIGNING'::new_propertystatus
            WHEN 'TAKEOVER' THEN 'COL_DOAS_SIGNING'::new_propertystatus
            ELSE 'PROPERTY_SOURCING'::new_propertystatus
        END
    """)
    
    # Update workflow_history table if it exists
    # First, add the new column
    op.add_column('workflow_history', sa.Column('from_status_new', new_status_enum, nullable=True))
    op.add_column('workflow_history', sa.Column('to_status_new', new_status_enum, nullable=True))
    
    # Migrate workflow_history data
    op.execute("""
        UPDATE workflow_history 
        SET from_status_new = CASE from_status::text
            WHEN 'PROPERTY_SOURCING' THEN 'PROPERTY_SOURCING'::new_propertystatus
            WHEN 'PROPERTY_STUDY' THEN 'PROPERTY_SCREENING_FUNG_SHUI'::new_propertystatus
            WHEN 'PBY_PREPARATION' THEN 'PBY_STUDY'::new_propertystatus
            WHEN 'COUNCIL_APPROVAL' THEN 'EXECOM'::new_propertystatus
            WHEN 'NEGOTIATION' THEN 'NEGOTIATION'::new_propertystatus
            WHEN 'DUE_DILIGENCE' THEN 'DUE_DILIGENCE'::new_propertystatus
            WHEN 'CONTRACT_SIGNING' THEN 'COL_DOAS_SIGNING'::new_propertystatus
            WHEN 'TAKEOVER' THEN 'COL_DOAS_SIGNING'::new_propertystatus
            ELSE NULL
        END
        WHERE from_status IS NOT NULL
    """)
    
    op.execute("""
        UPDATE workflow_history 
        SET to_status_new = CASE to_status::text
            WHEN 'PROPERTY_SOURCING' THEN 'PROPERTY_SOURCING'::new_propertystatus
            WHEN 'PROPERTY_STUDY' THEN 'PROPERTY_SCREENING_FUNG_SHUI'::new_propertystatus
            WHEN 'PBY_PREPARATION' THEN 'PBY_STUDY'::new_propertystatus
            WHEN 'COUNCIL_APPROVAL' THEN 'EXECOM'::new_propertystatus
            WHEN 'NEGOTIATION' THEN 'NEGOTIATION'::new_propertystatus
            WHEN 'DUE_DILIGENCE' THEN 'DUE_DILIGENCE'::new_propertystatus
            WHEN 'CONTRACT_SIGNING' THEN 'COL_DOAS_SIGNING'::new_propertystatus
            WHEN 'TAKEOVER' THEN 'COL_DOAS_SIGNING'::new_propertystatus
            ELSE NULL
        END
    """)
    
    # Drop old columns
    op.drop_column('properties', 'status')
    op.drop_column('workflow_history', 'from_status')
    op.drop_column('workflow_history', 'to_status')
    
    # Drop old enum type
    sa.Enum(name='propertystatus').drop(op.get_bind())
    
    # Rename new columns to original names
    op.alter_column('properties', 'status_new', new_column_name='status')
    op.alter_column('workflow_history', 'from_status_new', new_column_name='from_status')
    op.alter_column('workflow_history', 'to_status_new', new_column_name='to_status')
    
    # Rename enum type
    op.execute("ALTER TYPE new_propertystatus RENAME TO propertystatus")
    
    # Set not null constraint on status
    op.alter_column('properties', 'status', nullable=False)


def downgrade() -> None:
    # Create old enum type
    old_status_enum = postgresql.ENUM(
        'PROPERTY_SOURCING',
        'PROPERTY_STUDY',
        'PBY_PREPARATION',
        'COUNCIL_APPROVAL',
        'NEGOTIATION',
        'DUE_DILIGENCE',
        'CONTRACT_SIGNING',
        'TAKEOVER',
        name='old_propertystatus'
    )
    old_status_enum.create(op.get_bind())
    
    # Add temporary column with old enum
    op.add_column('properties', sa.Column('status_old', old_status_enum, nullable=True))
    
    # Migrate data back
    op.execute("""
        UPDATE properties 
        SET status_old = CASE status::text
            WHEN 'PROPERTY_SOURCING' THEN 'PROPERTY_SOURCING'::old_propertystatus
            WHEN 'PROPERTY_SCREENING_FUNG_SHUI' THEN 'PROPERTY_STUDY'::old_propertystatus
            WHEN 'PBY_STUDY' THEN 'PBY_PREPARATION'::old_propertystatus
            WHEN 'EXECOM' THEN 'COUNCIL_APPROVAL'::old_propertystatus
            WHEN 'BOARD_APPROVAL' THEN 'COUNCIL_APPROVAL'::old_propertystatus
            WHEN 'NEGOTIATION' THEN 'NEGOTIATION'::old_propertystatus
            WHEN 'DUE_DILIGENCE' THEN 'DUE_DILIGENCE'::old_propertystatus
            WHEN 'COL_DOAS_SIGNING' THEN 'CONTRACT_SIGNING'::old_propertystatus
            ELSE 'PROPERTY_SOURCING'::old_propertystatus
        END
    """)
    
    # Update workflow_history
    op.add_column('workflow_history', sa.Column('from_status_old', old_status_enum, nullable=True))
    op.add_column('workflow_history', sa.Column('to_status_old', old_status_enum, nullable=True))
    
    op.execute("""
        UPDATE workflow_history 
        SET from_status_old = CASE from_status::text
            WHEN 'PROPERTY_SOURCING' THEN 'PROPERTY_SOURCING'::old_propertystatus
            WHEN 'PROPERTY_SCREENING_FUNG_SHUI' THEN 'PROPERTY_STUDY'::old_propertystatus
            WHEN 'PBY_STUDY' THEN 'PBY_PREPARATION'::old_propertystatus
            WHEN 'EXECOM' THEN 'COUNCIL_APPROVAL'::old_propertystatus
            WHEN 'BOARD_APPROVAL' THEN 'COUNCIL_APPROVAL'::old_propertystatus
            WHEN 'NEGOTIATION' THEN 'NEGOTIATION'::old_propertystatus
            WHEN 'DUE_DILIGENCE' THEN 'DUE_DILIGENCE'::old_propertystatus
            WHEN 'COL_DOAS_SIGNING' THEN 'CONTRACT_SIGNING'::old_propertystatus
            ELSE NULL
        END
        WHERE from_status IS NOT NULL
    """)
    
    op.execute("""
        UPDATE workflow_history 
        SET to_status_old = CASE to_status::text
            WHEN 'PROPERTY_SOURCING' THEN 'PROPERTY_SOURCING'::old_propertystatus
            WHEN 'PROPERTY_SCREENING_FUNG_SHUI' THEN 'PROPERTY_STUDY'::old_propertystatus
            WHEN 'PBY_STUDY' THEN 'PBY_PREPARATION'::old_propertystatus
            WHEN 'EXECOM' THEN 'COUNCIL_APPROVAL'::old_propertystatus
            WHEN 'BOARD_APPROVAL' THEN 'COUNCIL_APPROVAL'::old_propertystatus
            WHEN 'NEGOTIATION' THEN 'NEGOTIATION'::old_propertystatus
            WHEN 'DUE_DILIGENCE' THEN 'DUE_DILIGENCE'::old_propertystatus
            WHEN 'COL_DOAS_SIGNING' THEN 'CONTRACT_SIGNING'::old_propertystatus
            ELSE NULL
        END
    """)
    
    # Drop new columns
    op.drop_column('properties', 'status')
    op.drop_column('workflow_history', 'from_status')
    op.drop_column('workflow_history', 'to_status')
    
    # Drop new enum
    sa.Enum(name='propertystatus').drop(op.get_bind())
    
    # Rename old columns
    op.alter_column('properties', 'status_old', new_column_name='status')
    op.alter_column('workflow_history', 'from_status_old', new_column_name='from_status')
    op.alter_column('workflow_history', 'to_status_old', new_column_name='to_status')
    
    # Rename enum type back
    op.execute("ALTER TYPE old_propertystatus RENAME TO propertystatus")
    
    # Set not null constraint
    op.alter_column('properties', 'status', nullable=False)

