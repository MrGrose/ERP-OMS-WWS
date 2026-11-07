from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from erp_oms_wms.db import Base
from erp_oms_wms.domains.inventory.models import new_uuid_str
from erp_oms_wms.domains.orders.enums import OrderStatus


class Order(Base):
    __tablename__ = "customer_order"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid_str)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, values_callable=lambda x: [e.value for e in x]),
        default=OrderStatus.DRAFT,
    )
    customer_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    lines: Mapped[list["OrderLine"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class OrderLine(Base):
    __tablename__ = "order_line"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_order_line_qty_positive"),
        CheckConstraint("quantity_shipped >= 0", name="ck_order_line_shipped_nonneg"),
        CheckConstraint("quantity_shipped <= quantity", name="ck_order_line_shipped_le_qty"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid_str)
    order_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("customer_order.id", ondelete="CASCADE"),
        nullable=False,
    )
    warehouse_id: Mapped[str] = mapped_column(String(64), nullable=False)
    sku: Mapped[str] = mapped_column(String(128), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_shipped: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unit_price_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reservation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    order: Mapped[Order] = relationship(back_populates="lines")
