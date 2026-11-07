"""customers, pricing, supplier products, order line prices

Revision ID: 20261107_0006
Revises: 20261107_0005
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261107_0006"
down_revision: str | Sequence[str] | None = "20261107_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    price_list_enum = sa.Enum("RETAIL", "WHOLESALE", "B2B", "SPECIAL", name="price_list")
    price_list_enum.create(op.get_bind(), checkfirst=True)
    price_list_type = sa.Enum(
        "RETAIL",
        "WHOLESALE",
        "B2B",
        "SPECIAL",
        name="price_list",
        create_type=False,
    )

    op.create_table(
        "customer",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=512), nullable=False),
        sa.Column("email", sa.String(length=256), nullable=True),
        sa.Column("price_list", price_list_type, nullable=False, server_default="RETAIL"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "product_price",
        sa.Column("price_list", price_list_type, nullable=False),
        sa.Column("sku", sa.String(length=128), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="RUB"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("amount_cents >= 0", name="ck_product_price_nonneg"),
        sa.PrimaryKeyConstraint("price_list", "sku"),
        sa.UniqueConstraint("price_list", "sku", name="uq_product_price_list_sku"),
    )
    op.create_table(
        "supplier_product",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("supplier_id", sa.String(length=36), nullable=False),
        sa.Column("sku", sa.String(length=128), nullable=False),
        sa.Column("supplier_sku", sa.String(length=128), nullable=False),
        sa.Column("purchase_price_cents", sa.Integer(), nullable=False),
        sa.Column("lead_time_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("purchase_price_cents >= 0", name="ck_supplier_price_nonneg"),
        sa.ForeignKeyConstraint(["supplier_id"], ["supplier.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("supplier_id", "sku", name="uq_supplier_product_sku"),
    )
    with op.batch_alter_table("order_line") as batch:
        batch.add_column(
            sa.Column("quantity_shipped", sa.Integer(), nullable=False, server_default="0")
        )
        batch.add_column(sa.Column("unit_price_cents", sa.Integer(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("order_line") as batch:
        batch.drop_column("unit_price_cents")
        batch.drop_column("quantity_shipped")
    op.drop_table("supplier_product")
    op.drop_table("product_price")
    op.drop_table("customer")
    op.execute("DROP TYPE IF EXISTS price_list")
