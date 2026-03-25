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
    op.add_column(
        "agents",
        sa.Column("agent_type", sa.String(length=50), nullable=False, server_default="general"),
    )
    op.add_column(
        "agents",
        sa.Column("stock_quantity", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "agents",
        sa.Column("stock_unit_price", sa.Integer(), nullable=False, server_default="800"),
    )


def downgrade() -> None:
    op.drop_column("agents", "stock_unit_price")
    op.drop_column("agents", "stock_quantity")
    op.drop_column("agents", "agent_type")
