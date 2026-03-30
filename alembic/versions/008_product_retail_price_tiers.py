"""Create product retail price tiers table

Revision ID: 008
Revises: 007
Create Date: 2026-03-30 03:20:00
"""

from alembic import op
import sqlalchemy as sa


revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "product_retail_price_tiers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("min_quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id", "min_quantity", name="uq_product_retail_price_tier_quantity"),
    )
    op.create_index(
        op.f("ix_product_retail_price_tiers_id"),
        "product_retail_price_tiers",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_product_retail_price_tiers_product_id"),
        "product_retail_price_tiers",
        ["product_id"],
        unique=False,
    )

    connection = op.get_bind()
    rows = connection.execute(
        sa.text(
            """
            SELECT id, retail_bulk_min_quantity, retail_bulk_unit_price
            FROM products
            WHERE retail_bulk_min_quantity IS NOT NULL
              AND retail_bulk_unit_price IS NOT NULL
            """
        )
    ).fetchall()
    for row in rows:
        connection.execute(
            sa.text(
                """
                INSERT INTO product_retail_price_tiers (product_id, min_quantity, unit_price)
                VALUES (:product_id, :min_quantity, :unit_price)
                """
            ),
            {
                "product_id": row.id,
                "min_quantity": row.retail_bulk_min_quantity,
                "unit_price": row.retail_bulk_unit_price,
            },
        )

    op.drop_column("products", "retail_bulk_unit_price")
    op.drop_column("products", "retail_bulk_min_quantity")


def downgrade() -> None:
    op.add_column("products", sa.Column("retail_bulk_min_quantity", sa.Integer(), nullable=True))
    op.add_column("products", sa.Column("retail_bulk_unit_price", sa.Integer(), nullable=True))

    connection = op.get_bind()
    rows = connection.execute(
        sa.text(
            """
            SELECT DISTINCT ON (product_id) product_id, min_quantity, unit_price
            FROM product_retail_price_tiers
            ORDER BY product_id, min_quantity ASC
            """
        )
    ).fetchall()
    for row in rows:
        connection.execute(
            sa.text(
                """
                UPDATE products
                SET retail_bulk_min_quantity = :min_quantity,
                    retail_bulk_unit_price = :unit_price
                WHERE id = :product_id
                """
            ),
            {
                "product_id": row.product_id,
                "min_quantity": row.min_quantity,
                "unit_price": row.unit_price,
            },
        )

    op.drop_index(op.f("ix_product_retail_price_tiers_product_id"), table_name="product_retail_price_tiers")
    op.drop_index(op.f("ix_product_retail_price_tiers_id"), table_name="product_retail_price_tiers")
    op.drop_table("product_retail_price_tiers")
