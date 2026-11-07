"""purchasing tables

Revision ID: 20261107_0004
Revises: 20261107_0003
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261107_0004"
down_revision: str | Sequence[str] | None = "20261107_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "purchase_order",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("supplier_id", sa.String(length=64), nullable=False),
        sa.Column(
            "status",
            sa.Enum("DRAFT", "CONFIRMED", "RECEIVED", "CANCELLED", name="purchase_order_status"),
            nullable=False,
            server_default="DRAFT",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "purchase_order_line",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("purchase_order_id", sa.String(length=36), nullable=False),
        sa.Column("warehouse_id", sa.String(length=64), nullable=False),
        sa.Column("sku", sa.String(length=128), nullable=False),
        sa.Column("quantity_ordered", sa.Integer(), nullable=False),
        sa.Column("quantity_received", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_order.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "goods_receipt",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("purchase_order_id", sa.String(length=36), nullable=False),
        sa.Column(
            "status",
            sa.Enum("DRAFT", "CONFIRMED", "CANCELLED", name="goods_receipt_status"),
            nullable=False,
            server_default="DRAFT",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_order.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_goods_receipt_po", "goods_receipt", ["purchase_order_id"])
    op.create_table(
        "goods_receipt_line",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("goods_receipt_id", sa.String(length=36), nullable=False),
        sa.Column("purchase_order_line_id", sa.String(length=36), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["goods_receipt_id"], ["goods_receipt.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["purchase_order_line_id"], ["purchase_order_line.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("goods_receipt_line")
    op.drop_index("ix_goods_receipt_po", table_name="goods_receipt")
    op.drop_table("goods_receipt")
    op.drop_table("purchase_order_line")
    op.drop_table("purchase_order")
    op.execute("DROP TYPE IF EXISTS goods_receipt_status")
    op.execute("DROP TYPE IF EXISTS purchase_order_status")
