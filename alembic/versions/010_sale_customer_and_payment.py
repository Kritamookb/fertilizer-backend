"""Add customers and sale metadata

Revision ID: 010
Revises: 009
Create Date: 2026-03-30 14:45:00
"""

from alembic import op
import sqlalchemy as sa


revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("agent_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_customers_id"), "customers", ["id"], unique=False)
    op.create_index(op.f("ix_customers_agent_id"), "customers", ["agent_id"], unique=False)
    op.create_index(op.f("ix_customers_name"), "customers", ["name"], unique=False)
    op.create_index(op.f("ix_customers_phone"), "customers", ["phone"], unique=False)

    op.add_column("sales", sa.Column("customer_id", sa.Integer(), nullable=True))
    op.add_column(
        "sales",
        sa.Column("sale_type", sa.String(length=50), nullable=False, server_default="agent_pickup"),
    )
    op.add_column(
        "sales",
        sa.Column("payment_method", sa.String(length=50), nullable=False, server_default="transfer"),
    )
    op.create_index(op.f("ix_sales_customer_id"), "sales", ["customer_id"], unique=False)
    op.create_foreign_key("fk_sales_customer_id", "sales", "customers", ["customer_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_sales_customer_id", "sales", type_="foreignkey")
    op.drop_index(op.f("ix_sales_customer_id"), table_name="sales")
    op.drop_column("sales", "payment_method")
    op.drop_column("sales", "sale_type")
    op.drop_column("sales", "customer_id")
    op.drop_index(op.f("ix_customers_phone"), table_name="customers")
    op.drop_index(op.f("ix_customers_name"), table_name="customers")
    op.drop_index(op.f("ix_customers_agent_id"), table_name="customers")
    op.drop_index(op.f("ix_customers_id"), table_name="customers")
    op.drop_table("customers")
