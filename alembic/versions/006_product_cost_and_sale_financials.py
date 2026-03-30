"""Add product cost, retail price, and sale financial snapshots

Revision ID: 006
Revises: 005
Create Date: 2026-03-30 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column("cost_price_hq", sa.Integer(), nullable=False, server_default="550"),
    )
    op.add_column(
        "products",
        sa.Column("default_price_retail", sa.Integer(), nullable=False, server_default="890"),
    )
    op.add_column(
        "sales",
        sa.Column("unit_price", sa.Integer(), nullable=False, server_default="800"),
    )
    op.add_column(
        "sales",
        sa.Column("unit_cost", sa.Integer(), nullable=False, server_default="550"),
    )
    op.add_column(
        "sales",
        sa.Column("total_amount", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "sales",
        sa.Column("total_cost", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "sales",
        sa.Column("gross_profit", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("sales", "gross_profit")
    op.drop_column("sales", "total_cost")
    op.drop_column("sales", "total_amount")
    op.drop_column("sales", "unit_cost")
    op.drop_column("sales", "unit_price")
    op.drop_column("products", "default_price_retail")
    op.drop_column("products", "cost_price_hq")
