import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from erp_oms_wms.db import Base
from erp_oms_wms.domains.returns.enums import ReturnStatus


def new_uuid_str() -> str:
    return str(uuid.uuid4())


class ReturnRequest(Base):
    __tablename__ = "return_request"
    __table_args__ = (CheckConstraint("quantity > 0", name="ck_return_qty_positive"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid_str)
    order_id: Mapped[str] = mapped_column(String(36), nullable=False)
    warehouse_id: Mapped[str] = mapped_column(String(64), nullable=False)
    sku: Mapped[str] = mapped_column(String(128), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ReturnStatus] = mapped_column(
        Enum(ReturnStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ReturnStatus.INITIATED,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
