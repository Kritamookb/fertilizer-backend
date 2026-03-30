"""Add product retail bulk pricing fields

Revision ID: 007
Revises: 006
Create Date: 2026-03-30 00:30:00
"""

from alembic import op
import sqlalchemy as sa


revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column("retail_bulk_min_quantity", sa.Integer(), nullable=True),
    )
    op.add_column(
        "products",
        sa.Column("retail_bulk_unit_price", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("products", "retail_bulk_unit_price")
    op.drop_column("products", "retail_bulk_min_quantity")
