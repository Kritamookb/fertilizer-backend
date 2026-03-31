"""add agent code and address fields

Revision ID: 012_agent_code_and_address
Revises: 011_agent_profile_fields
Create Date: 2026-03-31 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "012_agent_code_and_address"
down_revision = "011_agent_profile_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("agents", sa.Column("agent_code", sa.String(length=100), nullable=True))
    op.add_column("agents", sa.Column("address", sa.String(length=1000), nullable=True))
    op.create_index("ix_agents_agent_code", "agents", ["agent_code"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_agents_agent_code", table_name="agents")
    op.drop_column("agents", "address")
    op.drop_column("agents", "agent_code")
