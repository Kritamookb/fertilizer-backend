"""Add agent type and stock fields

Revision ID: 002
Revises: 001
Create Date: 2026-03-25 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS agent_type VARCHAR(50) NOT NULL DEFAULT 'general'")
    op.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS stock_quantity INTEGER NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS stock_unit_price INTEGER NOT NULL DEFAULT 800")


def downgrade() -> None:
    op.drop_column("agents", "stock_unit_price")
    op.drop_column("agents", "stock_quantity")
    op.drop_column("agents", "agent_type")
