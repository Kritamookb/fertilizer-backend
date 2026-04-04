"""Add agent profile fields

Revision ID: 011
Revises: 010
Create Date: 2026-03-30 15:10:00
"""

from alembic import op
import sqlalchemy as sa


revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS nickname VARCHAR(255)")
    op.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS line_id VARCHAR(100)")
    op.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS bank_name VARCHAR(255)")
    op.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS bank_account_name VARCHAR(255)")
    op.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS bank_account_number VARCHAR(100)")


def downgrade() -> None:
    op.drop_column("agents", "bank_account_number")
    op.drop_column("agents", "bank_account_name")
    op.drop_column("agents", "bank_name")
    op.drop_column("agents", "line_id")
    op.drop_column("agents", "nickname")
