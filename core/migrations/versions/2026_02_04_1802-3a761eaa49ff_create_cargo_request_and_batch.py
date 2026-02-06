"""Create cargo request and batch

Revision ID: 3a761eaa49ff
Revises: 
Create Date: 2026-02-04 18:02:25.311760+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '3a761eaa49ff'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    provider_type = postgresql.ENUM('bedrock', 'anthropic', name='provider_type', create_type=False)
    provider_type.create(op.get_bind(), checkfirst=True)
    
    cargo_status = postgresql.ENUM(
        'pending', 'batched', 'processing', 'completed', 'failed',
        'callback_pending', 'callback_delivered', 'callback_failed',
        name='cargo_status', create_type=False
    )
    cargo_status.create(op.get_bind(), checkfirst=True)
    
    batch_status = postgresql.ENUM(
        'pending', 'ready', 'submitted', 'processing', 'completed',
        'partially_completed', 'failed', 'cancelled',
        name='batch_status', create_type=False
    )
    batch_status.create(op.get_bind(), checkfirst=True)
    
    callback_status = postgresql.ENUM(
        'pending', 'retrying', 'delivered', 'failed', 'manual_retry',
        name='callback_status', create_type=False
    )
    callback_status.create(op.get_bind(), checkfirst=True)

    # Create batch_jobs table
    op.create_table(
        'batch_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('provider', postgresql.ENUM('bedrock', 'anthropic', name='provider_type', create_type=False), nullable=False),
        sa.Column('provider_job_id', sa.String(256), nullable=True),
        sa.Column('status', postgresql.ENUM('pending', 'ready', 'submitted', 'processing', 'completed', 'partially_completed', 'failed', 'cancelled', name='batch_status', create_type=False), nullable=False, server_default='pending'),
        sa.Column('request_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for batch_jobs
    op.create_index('idx_batch_jobs_status', 'batch_jobs', ['status'])
    op.create_index('idx_batch_jobs_provider_status', 'batch_jobs', ['provider', 'status'])
    op.create_index('idx_batch_jobs_provider_job_id', 'batch_jobs', ['provider_job_id'])
    op.create_index('idx_batch_jobs_created_at', 'batch_jobs', ['created_at'])

    # Create cargo_requests table
    op.create_table(
        'cargo_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('cargo_id', sa.String(64), nullable=False),
        sa.Column('provider', postgresql.ENUM('bedrock', 'anthropic', name='provider_type', create_type=False), nullable=False),
        sa.Column('model', sa.String(128), nullable=False),
        sa.Column('params', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('callback_url', sa.String(2048), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'batched', 'processing', 'completed', 'failed', 'callback_pending', 'callback_delivered', 'callback_failed', name='cargo_status', create_type=False), nullable=False, server_default='pending'),
        sa.Column('batch_job_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['batch_job_id'], ['batch_jobs.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cargo_id')
    )
    
    # Create indexes for cargo_requests
    op.create_index('idx_cargo_requests_status', 'cargo_requests', ['status'])
    op.create_index('idx_cargo_requests_provider_status', 'cargo_requests', ['provider', 'status'])
    op.create_index('idx_cargo_requests_batch_job_id', 'cargo_requests', ['batch_job_id'])
    op.create_index('idx_cargo_requests_created_at', 'cargo_requests', ['created_at'])

    # Create cargo_results table
    op.create_table(
        'cargo_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('cargo_request_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('response', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['cargo_request_id'], ['cargo_requests.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cargo_request_id')
    )
    
    # Create indexes for cargo_results
    op.create_index('idx_cargo_results_cargo_request_id', 'cargo_results', ['cargo_request_id'])
    op.create_index('idx_cargo_results_expires_at', 'cargo_results', ['expires_at'])

    # Create callback_deliveries table
    op.create_table(
        'callback_deliveries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('cargo_request_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'retrying', 'delivered', 'failed', 'manual_retry', name='callback_status', create_type=False), nullable=False, server_default='pending'),
        sa.Column('attempt_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_attempt_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('http_status_code', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['cargo_request_id'], ['cargo_requests.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cargo_request_id')
    )
    
    # Create indexes for callback_deliveries
    op.create_index('idx_callback_deliveries_status', 'callback_deliveries', ['status'])
    op.create_index(
        'idx_callback_deliveries_next_retry_at',
        'callback_deliveries',
        ['next_retry_at'],
        postgresql_where=sa.text("status IN ('pending', 'retrying', 'manual_retry')")
    )
    op.create_index('idx_callback_deliveries_cargo_request_id', 'callback_deliveries', ['cargo_request_id'])

    # Create trigger function for updated_at
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Apply trigger to cargo_requests
    op.execute("""
        CREATE TRIGGER update_cargo_requests_updated_at
            BEFORE UPDATE ON cargo_requests
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    # Drop trigger
    op.execute("DROP TRIGGER IF EXISTS update_cargo_requests_updated_at ON cargo_requests;")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")
    
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('callback_deliveries')
    op.drop_table('cargo_results')
    op.drop_table('cargo_requests')
    op.drop_table('batch_jobs')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS callback_status;")
    op.execute("DROP TYPE IF EXISTS cargo_status;")
    op.execute("DROP TYPE IF EXISTS batch_status;")
    op.execute("DROP TYPE IF EXISTS provider_type;")
