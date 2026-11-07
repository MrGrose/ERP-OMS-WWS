"""invoices and payments

Revision ID: 20261107_0003
Revises: 20261107_0002
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261107_0003"
down_revision: str | Sequence[str] | None = "20261107_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "invoice",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "ISSUED",
                "PENDING_PAYMENT",
                "PAID",
                "EXPIRED",
                name="invoice_status",
            ),
            nullable=False,
        ),
        sa.Column("order_id", sa.String(length=36), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
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
    op.create_index("ix_invoice_order_id", "invoice", ["order_id"])
    op.create_table(
        "payment_attempt",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("invoice_id", sa.String(length=36), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "CREATED",
                "PENDING",
                "SUCCEEDED",
                "FAILED",
                "CANCELLED",
                name="payment_attempt_status",
            ),
            nullable=False,
        ),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("external_payment_id", sa.String(length=128), nullable=True),
        sa.Column("external_event_id", sa.String(length=128), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["invoice_id"], ["invoice.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_event_id", name="uq_payment_external_event_id"),
    )
    op.create_index("ix_payment_attempt_invoice_id", "payment_attempt", ["invoice_id"])


def downgrade() -> None:
    op.drop_index("ix_payment_attempt_invoice_id", table_name="payment_attempt")
    op.drop_table("payment_attempt")
    op.drop_index("ix_invoice_order_id", table_name="invoice")
    op.drop_table("invoice")
    op.execute("DROP TYPE IF EXISTS payment_attempt_status")
    op.execute("DROP TYPE IF EXISTS invoice_status")
