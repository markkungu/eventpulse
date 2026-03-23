"""create events table

Revision ID: 001
Revises:
Create Date: 2026-03-23
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            type VARCHAR(100) NOT NULL,
            source VARCHAR(100) NOT NULL,
            payload JSONB NOT NULL DEFAULT '{}',
            status VARCHAR(20) NOT NULL DEFAULT 'queued',
            result JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            processed_at TIMESTAMPTZ
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_events_status ON events(status)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(type)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at DESC)")


def downgrade() -> None:
    op.drop_table("events")
