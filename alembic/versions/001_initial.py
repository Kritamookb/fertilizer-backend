"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-03-24 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "admin_users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
    )
    op.create_index("ix_admin_users_id", "admin_users", ["id"], unique=False)
    op.create_index("ix_admin_users_username", "admin_users", ["username"], unique=True)
    op.create_index("ix_admin_users_email", "admin_users", ["email"], unique=True)

    op.create_table(
        "agents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=False),
        sa.Column("referred_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.ForeignKeyConstraint(["referred_by_id"], ["agents.id"]),
    )
    op.create_index("ix_agents_id", "agents", ["id"], unique=False)
    op.create_index("ix_agents_name", "agents", ["name"], unique=False)
    op.create_index("ix_agents_phone", "agents", ["phone"], unique=True)
    op.create_index("ix_agents_referred_by_id", "agents", ["referred_by_id"], unique=False)

    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("unit", sa.String(length=50), nullable=False),
    )
    op.create_index("ix_products_id", "products", ["id"], unique=False)
    op.create_index("ix_products_name", "products", ["name"], unique=True)

    op.create_table(
        "sales",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("agent_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("sale_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
    )
    op.create_index("ix_sales_id", "sales", ["id"], unique=False)
    op.create_index("ix_sales_agent_id", "sales", ["agent_id"], unique=False)
    op.create_index("ix_sales_product_id", "sales", ["product_id"], unique=False)
    op.create_index("ix_sales_sale_date", "sales", ["sale_date"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_sales_sale_date", table_name="sales")
    op.drop_index("ix_sales_product_id", table_name="sales")
    op.drop_index("ix_sales_agent_id", table_name="sales")
    op.drop_index("ix_sales_id", table_name="sales")
    op.drop_table("sales")

    op.drop_index("ix_products_name", table_name="products")
    op.drop_index("ix_products_id", table_name="products")
    op.drop_table("products")

    op.drop_index("ix_agents_referred_by_id", table_name="agents")
    op.drop_index("ix_agents_phone", table_name="agents")
    op.drop_index("ix_agents_name", table_name="agents")
    op.drop_index("ix_agents_id", table_name="agents")
    op.drop_table("agents")

    op.drop_index("ix_admin_users_email", table_name="admin_users")
    op.drop_index("ix_admin_users_username", table_name="admin_users")
    op.drop_index("ix_admin_users_id", table_name="admin_users")
    op.drop_table("admin_users")
