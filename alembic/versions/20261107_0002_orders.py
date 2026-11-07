"""customer orders

Revision ID: 20261107_0002
Revises: 20261107_0001
Create Date: 2026-11-07

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261107_0002"
down_revision: str | Sequence[str] | None = "20261107_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "customer_order",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "DRAFT",
                "CONFIRMED",
                "RESERVED",
                "PAID",
                "ASSEMBLING",
                "SHIPPED",
                "COMPLETED",
                "CANCELLED",
                name="order_status",
            ),
            nullable=False,
            server_default="DRAFT",
        ),
        sa.Column("customer_id", sa.String(length=128), nullable=True),
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
    op.create_table(
        "order_line",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("order_id", sa.String(length=36), nullable=False),
        sa.Column("warehouse_id", sa.String(length=64), nullable=False),
        sa.Column("sku", sa.String(length=128), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("reservation_id", sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(["order_id"], ["customer_order.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("order_line")
    op.drop_table("customer_order")
    op.execute("DROP TYPE IF EXISTS order_status")
