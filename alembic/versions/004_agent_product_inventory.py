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
    op.execute("""
        CREATE TABLE IF NOT EXISTS agent_inventories (
            id SERIAL NOT NULL,
            agent_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER DEFAULT '0' NOT NULL,
            unit_price INTEGER NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY(agent_id) REFERENCES agents (id),
            FOREIGN KEY(product_id) REFERENCES products (id),
            CONSTRAINT uq_agent_product_inventory UNIQUE (agent_id, product_id)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_agent_inventories_id ON agent_inventories (id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_agent_inventories_agent_id ON agent_inventories (agent_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_agent_inventories_product_id ON agent_inventories (product_id)")


def downgrade() -> None:
    op.drop_index("ix_agent_inventories_product_id", table_name="agent_inventories")
    op.drop_index("ix_agent_inventories_agent_id", table_name="agent_inventories")
    op.drop_index("ix_agent_inventories_id", table_name="agent_inventories")
    op.drop_table("agent_inventories")
