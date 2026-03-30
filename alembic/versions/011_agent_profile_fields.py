"""Add agent profile fields

Revision ID: 011
Revises: 010
Create Date: 2026-03-30 15:10:00
"""

from alembic import op
import sqlalchemy as sa


revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("agents", sa.Column("nickname", sa.String(length=255), nullable=True))
    op.add_column("agents", sa.Column("line_id", sa.String(length=100), nullable=True))
    op.add_column("agents", sa.Column("bank_name", sa.String(length=255), nullable=True))
    op.add_column("agents", sa.Column("bank_account_name", sa.String(length=255), nullable=True))
    op.add_column("agents", sa.Column("bank_account_number", sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column("agents", "bank_account_number")
    op.drop_column("agents", "bank_account_name")
    op.drop_column("agents", "bank_name")
    op.drop_column("agents", "line_id")
    op.drop_column("agents", "nickname")
