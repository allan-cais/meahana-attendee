"""Migrate to Supabase database

Revision ID: 004
Revises: 003
Create Date: 2025-01-27 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Migrate to Supabase - no schema changes needed, just connection update"""
    # This migration is primarily for documentation purposes
    # The actual migration happens by updating the DATABASE_URL environment variable
    # from local PostgreSQL to Supabase connection string
    
    # Ensure all tables exist (they should from previous migrations)
    # Supabase will automatically create the schema if it doesn't exist
    
    # No schema changes needed - Supabase is PostgreSQL compatible
    pass


def downgrade() -> None:
    """Revert to local PostgreSQL - no schema changes needed"""
    # This would involve changing the DATABASE_URL back to local PostgreSQL
    # No schema changes needed - just connection string update
    pass
