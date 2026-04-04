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
    op.execute("""
        CREATE TABLE IF NOT EXISTS product_retail_price_tiers (
            id SERIAL NOT NULL,
            product_id INTEGER NOT NULL,
            min_quantity INTEGER NOT NULL,
            unit_price INTEGER NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY(product_id) REFERENCES products (id),
            CONSTRAINT uq_product_retail_price_tier_quantity UNIQUE (product_id, min_quantity)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_product_retail_price_tiers_id ON product_retail_price_tiers (id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_product_retail_price_tiers_product_id ON product_retail_price_tiers (product_id)")

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
