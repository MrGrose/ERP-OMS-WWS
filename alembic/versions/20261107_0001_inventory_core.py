"""inventory core tables

Revision ID: 20261107_0001
Revises:
Create Date: 2026-11-07

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261107_0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "inventory_level",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("warehouse_id", sa.String(length=64), nullable=False),
        sa.Column("sku", sa.String(length=128), nullable=False),
        sa.Column("on_hand", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reserved", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("on_hand >= 0", name="ck_inventory_on_hand_nonneg"),
        sa.CheckConstraint("reserved >= 0", name="ck_inventory_reserved_nonneg"),
        sa.CheckConstraint("reserved <= on_hand", name="ck_inventory_reserved_le_on_hand"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("warehouse_id", "sku", name="uq_inventory_level_wh_sku"),
    )
    op.create_table(
        "stock_movement",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "movement_type",
            sa.Enum(
                "RECEIPT",
                "RESERVATION",
                "RELEASE",
                "SHIPMENT",
                "RETURN",
                "ADJUSTMENT",
                "TRANSFER",
                name="stock_movement_type",
            ),
            nullable=False,
        ),
        sa.Column("warehouse_id", sa.String(length=64), nullable=False),
        sa.Column("sku", sa.String(length=128), nullable=False),
        sa.Column("on_hand_delta", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reserved_delta", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reference_type", sa.String(length=64), nullable=True),
        sa.Column("reference_id", sa.String(length=128), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_stock_movement_wh_sku", "stock_movement", ["warehouse_id", "sku"])
    op.create_table(
        "reservation",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("order_id", sa.String(length=128), nullable=False),
        sa.Column("warehouse_id", sa.String(length=64), nullable=False),
        sa.Column("sku", sa.String(length=128), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "ACTIVE", "SHIPPED", "RELEASED", "PARTIALLY_SHIPPED", name="reservation_status"
            ),
            nullable=False,
            server_default="ACTIVE",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reservation_order", "reservation", ["order_id"])


def downgrade() -> None:
    op.drop_index("ix_reservation_order", table_name="reservation")
    op.drop_table("reservation")
    op.drop_index("ix_stock_movement_wh_sku", table_name="stock_movement")
    op.drop_table("stock_movement")
    op.drop_table("inventory_level")
    op.execute("DROP TYPE IF EXISTS reservation_status")
    op.execute("DROP TYPE IF EXISTS stock_movement_type")
