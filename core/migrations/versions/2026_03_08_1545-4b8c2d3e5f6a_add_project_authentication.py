"""Add project authentication tables and project_id to cargo_requests

Revision ID: 4b8c2d3e5f6a
Revises: 3a761eaa49ff
Create Date: 2026-03-08 15:45:00.000000+00:00

This migration adds:
1. projects table - for multi-tenant project management
2. api_keys table - for project API key authentication
3. project_id column to cargo_requests - to associate cargo with projects

Note: This migration assumes cargo_requests table is empty or will be cleared.
      project_id is added as NOT NULL directly.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '4b8c2d3e5f6a'
down_revision: Union[str, Sequence[str], None] = '3a761eaa49ff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ============ Create projects table ============
    op.create_table(
        'projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(63), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    
    # Create indexes for projects
    op.create_index('idx_projects_slug', 'projects', ['slug'])
    op.create_index('idx_projects_is_active', 'projects', ['is_active'])
    
    # Apply updated_at trigger to projects
    op.execute("""
        CREATE TRIGGER update_projects_updated_at
            BEFORE UPDATE ON projects
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)

    # ============ Create api_keys table ============
    op.create_table(
        'api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('key_prefix', sa.String(12), nullable=False),
        sa.Column('key_hash', sa.String(64), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_hash')
    )
    
    # Create indexes for api_keys
    op.create_index('idx_api_keys_project_id', 'api_keys', ['project_id'])
    op.create_index('idx_api_keys_key_hash', 'api_keys', ['key_hash'])
    op.create_index(
        'idx_api_keys_active',
        'api_keys',
        ['is_active'],
        postgresql_where=sa.text("is_active = true")
    )

    # ============ Add project_id to cargo_requests ============
    # Add as NOT NULL directly (assumes table is empty or will be cleared)
    op.add_column(
        'cargo_requests',
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False)
    )
    
    # Create foreign key constraint
    op.create_foreign_key(
        'fk_cargo_requests_project_id',
        'cargo_requests',
        'projects',
        ['project_id'],
        ['id']
    )
    
    # Create indexes for project_id
    op.create_index('idx_cargo_requests_project_id', 'cargo_requests', ['project_id'])
    op.create_index('idx_cargo_requests_project_status', 'cargo_requests', ['project_id', 'status'])


def downgrade() -> None:
    # Drop indexes on cargo_requests
    op.drop_index('idx_cargo_requests_project_status', table_name='cargo_requests')
    op.drop_index('idx_cargo_requests_project_id', table_name='cargo_requests')
    
    # Drop foreign key constraint
    op.drop_constraint('fk_cargo_requests_project_id', 'cargo_requests', type_='foreignkey')
    
    # Drop project_id column
    op.drop_column('cargo_requests', 'project_id')
    
    # Drop api_keys table
    op.drop_index('idx_api_keys_active', table_name='api_keys')
    op.drop_index('idx_api_keys_key_hash', table_name='api_keys')
    op.drop_index('idx_api_keys_project_id', table_name='api_keys')
    op.drop_table('api_keys')
    
    # Drop trigger on projects
    op.execute("DROP TRIGGER IF EXISTS update_projects_updated_at ON projects;")
    
    # Drop projects table
    op.drop_index('idx_projects_is_active', table_name='projects')
    op.drop_index('idx_projects_slug', table_name='projects')
    op.drop_table('projects')
