"""order_line ship quantity constraints

Revision ID: 20261107_0007
Revises: 20261107_0006
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20261107_0007"
down_revision: str | Sequence[str] | None = "20261107_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("order_line") as batch:
        batch.create_check_constraint("ck_order_line_qty_positive", "quantity > 0")
        batch.create_check_constraint("ck_order_line_shipped_nonneg", "quantity_shipped >= 0")
        batch.create_check_constraint(
            "ck_order_line_shipped_le_qty", "quantity_shipped <= quantity"
        )


def downgrade() -> None:
    with op.batch_alter_table("order_line") as batch:
        batch.drop_constraint("ck_order_line_shipped_le_qty", type_="check")
        batch.drop_constraint("ck_order_line_shipped_nonneg", type_="check")
        batch.drop_constraint("ck_order_line_qty_positive", type_="check")
