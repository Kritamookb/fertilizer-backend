"""Add agent product inventory table

Revision ID: 004
Revises: 003
Create Date: 2026-03-25 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_inventories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("agent_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unit_price", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.UniqueConstraint("agent_id", "product_id", name="uq_agent_product_inventory"),
    )
    op.create_index("ix_agent_inventories_id", "agent_inventories", ["id"], unique=False)
    op.create_index("ix_agent_inventories_agent_id", "agent_inventories", ["agent_id"], unique=False)
    op.create_index("ix_agent_inventories_product_id", "agent_inventories", ["product_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_agent_inventories_product_id", table_name="agent_inventories")
    op.drop_index("ix_agent_inventories_agent_id", table_name="agent_inventories")
    op.drop_index("ix_agent_inventories_id", table_name="agent_inventories")
    op.drop_table("agent_inventories")
