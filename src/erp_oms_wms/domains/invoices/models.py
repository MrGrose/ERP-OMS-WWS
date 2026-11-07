from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from erp_oms_wms.db import Base
from erp_oms_wms.domains.inventory.models import new_uuid_str
from erp_oms_wms.domains.invoices.enums import InvoiceStatus


class Invoice(Base):
    __tablename__ = "invoice"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid_str)
    order_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus, values_callable=lambda x: [e.value for e in x]),
        default=InvoiceStatus.ISSUED,
    )
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="RUB")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
