"""Add product default prices

Revision ID: 005
Revises: 004
Create Date: 2026-03-25 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column("default_price_general", sa.Integer(), nullable=False, server_default="800"),
    )
    op.add_column(
        "products",
        sa.Column("default_price_sub_center", sa.Integer(), nullable=False, server_default="770"),
    )


def downgrade() -> None:
    op.drop_column("products", "default_price_sub_center")
    op.drop_column("products", "default_price_general")
