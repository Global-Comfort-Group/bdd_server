"""create activity logs table

Revision ID: 20251003_170757
Revises: 
Create Date: 2025-10-03 17:07:57

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251003_170757'
down_revision = 'f3950a9ad6f4'  # Previous migration (duplicate tracking)
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create activity_logs table
    op.create_table(
        'activity_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.Enum(
            'LOGIN', 'LOGOUT', 'CREATE', 'READ', 'UPDATE', 'DELETE',
            'ACTIVATE', 'DEACTIVATE', 'ROLE_CHANGE', 'PASSWORD_CHANGE',
            'EXPORT', 'APPROVE', 'REJECT', 'STATUS_CHANGE',
            name='activityaction'
        ), nullable=False),
        sa.Column('resource_type', sa.Enum(
            'USER', 'PROPERTY', 'NEGO_TABLE', 'NEGOTIATION_CHRONICLE',
            'SYSTEM', 'DUPLICATE', 'NOTIFICATION',
            name='resourcetype'
        ), nullable=False),
        sa.Column('resource_id', sa.Integer(), nullable=True),
        sa.Column('details', sa.Text(), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='fk_activity_logs_user_id', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better query performance
    op.create_index('ix_activity_logs_user_id', 'activity_logs', ['user_id'])
    op.create_index('ix_activity_logs_action', 'activity_logs', ['action'])
    op.create_index('ix_activity_logs_resource_type', 'activity_logs', ['resource_type'])
    op.create_index('ix_activity_logs_resource_id', 'activity_logs', ['resource_id'])
    op.create_index('ix_activity_logs_created_at', 'activity_logs', ['created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_activity_logs_created_at', table_name='activity_logs')
    op.drop_index('ix_activity_logs_resource_id', table_name='activity_logs')
    op.drop_index('ix_activity_logs_resource_type', table_name='activity_logs')
    op.drop_index('ix_activity_logs_action', table_name='activity_logs')
    op.drop_index('ix_activity_logs_user_id', table_name='activity_logs')
    
    # Drop table
    op.drop_table('activity_logs')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS activityaction')
    op.execute('DROP TYPE IF EXISTS resourcetype')

