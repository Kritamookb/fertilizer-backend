"""Add product commission flag

Revision ID: 003
Revises: 002
Create Date: 2026-03-25 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column("is_commissionable", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )


def downgrade() -> None:
    op.drop_column("products", "is_commissionable")
