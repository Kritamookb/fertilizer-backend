"""Add stock transfer history

Revision ID: 012
Revises: 011
Create Date: 2026-03-30 15:55:00
"""

from alembic import op
import sqlalchemy as sa


revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS stock_transfers (
            id SERIAL NOT NULL,
            agent_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            direction VARCHAR(50) NOT NULL,
            reason VARCHAR(50) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            FOREIGN KEY(agent_id) REFERENCES agents (id),
            FOREIGN KEY(product_id) REFERENCES products (id)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_stock_transfers_id ON stock_transfers (id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_stock_transfers_agent_id ON stock_transfers (agent_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_stock_transfers_product_id ON stock_transfers (product_id)")


def downgrade() -> None:
    op.drop_index(op.f("ix_stock_transfers_product_id"), table_name="stock_transfers")
    op.drop_index(op.f("ix_stock_transfers_agent_id"), table_name="stock_transfers")
    op.drop_index(op.f("ix_stock_transfers_id"), table_name="stock_transfers")
    op.drop_table("stock_transfers")
