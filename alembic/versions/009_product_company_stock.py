"""Add company stock quantity to products

Revision ID: 009
Revises: 008
Create Date: 2026-03-30 14:20:00
"""

from alembic import op
import sqlalchemy as sa


revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column("company_stock_quantity", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("products", "company_stock_quantity")
