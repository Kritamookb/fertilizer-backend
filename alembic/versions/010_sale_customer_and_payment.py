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
    op.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id SERIAL NOT NULL,
            agent_id INTEGER NOT NULL,
            name VARCHAR(255) NOT NULL,
            phone VARCHAR(50),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            PRIMARY KEY (id),
            FOREIGN KEY(agent_id) REFERENCES agents (id)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_customers_id ON customers (id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_customers_agent_id ON customers (agent_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_customers_name ON customers (name)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_customers_phone ON customers (phone)")

    op.execute("ALTER TABLE sales ADD COLUMN IF NOT EXISTS customer_id INTEGER")
    op.execute("ALTER TABLE sales ADD COLUMN IF NOT EXISTS sale_type VARCHAR(50) NOT NULL DEFAULT 'agent_pickup'")
    op.execute("ALTER TABLE sales ADD COLUMN IF NOT EXISTS payment_method VARCHAR(50) NOT NULL DEFAULT 'transfer'")
    op.execute("CREATE INDEX IF NOT EXISTS ix_sales_customer_id ON sales (customer_id)")
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'fk_sales_customer_id'
            ) THEN
                ALTER TABLE sales ADD CONSTRAINT fk_sales_customer_id
                    FOREIGN KEY (customer_id) REFERENCES customers (id);
            END IF;
        END $$
    """)


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
