import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from erp_oms_wms.db import Base
from erp_oms_wms.domains.transfers.enums import WarehouseTransferStatus


def new_uuid_str() -> str:
    return str(uuid.uuid4())


class WarehouseTransfer(Base):
    __tablename__ = "warehouse_transfer"
    __table_args__ = (CheckConstraint("quantity > 0", name="ck_transfer_qty_positive"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid_str)
    from_warehouse_id: Mapped[str] = mapped_column(String(64), nullable=False)
    to_warehouse_id: Mapped[str] = mapped_column(String(64), nullable=False)
    sku: Mapped[str] = mapped_column(String(128), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[WarehouseTransferStatus] = mapped_column(
        Enum(WarehouseTransferStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=WarehouseTransferStatus.DRAFT,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
