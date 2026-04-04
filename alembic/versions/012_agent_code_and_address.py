"""add agent code and address fields

Revision ID: 013
Revises: 012
Create Date: 2026-03-31 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS agent_code VARCHAR(100)")
    op.execute("ALTER TABLE agents ADD COLUMN IF NOT EXISTS address VARCHAR(1000)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_agents_agent_code ON agents (agent_code)")


def downgrade() -> None:
    op.drop_index("ix_agents_agent_code", table_name="agents")
    op.drop_column("agents", "address")
    op.drop_column("agents", "agent_code")
