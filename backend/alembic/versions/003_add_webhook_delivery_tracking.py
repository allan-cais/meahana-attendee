"""Add webhook delivery tracking columns

Revision ID: 003
Revises: 002
Create Date: 2025-08-18 13:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add webhook delivery tracking columns to webhook_events table
    op.add_column('webhook_events', sa.Column('delivery_status', sa.String(), nullable=True, server_default='pending'))
    op.add_column('webhook_events', sa.Column('delivery_attempts', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('webhook_events', sa.Column('last_delivery_attempt', sa.DateTime(timezone=True), nullable=True))
    op.add_column('webhook_events', sa.Column('delivery_error', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove webhook delivery tracking columns
    op.drop_column('webhook_events', 'delivery_error')
    op.drop_column('webhook_events', 'last_delivery_attempt')
    op.drop_column('webhook_events', 'delivery_attempts')
    op.drop_column('webhook_events', 'delivery_status') 