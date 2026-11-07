from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from erp_oms_wms.db import Base
from erp_oms_wms.domains.inventory.models import new_uuid_str
from erp_oms_wms.domains.purchasing.enums import GoodsReceiptStatus, PurchaseOrderStatus


class PurchaseOrder(Base):
    __tablename__ = "purchase_order"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid_str)
    supplier_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        Enum(PurchaseOrderStatus, values_callable=lambda x: [e.value for e in x]),
        default=PurchaseOrderStatus.DRAFT,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )


class PurchaseOrderLine(Base):
    __tablename__ = "purchase_order_line"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid_str)
    purchase_order_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("purchase_order.id", ondelete="CASCADE"),
        nullable=False,
    )
    warehouse_id: Mapped[str] = mapped_column(String(64), nullable=False)
    sku: Mapped[str] = mapped_column(String(128), nullable=False)
    quantity_ordered: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_received: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    purchase_order: Mapped[PurchaseOrder] = relationship(back_populates="lines")


class GoodsReceipt(Base):
    __tablename__ = "goods_receipt"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid_str)
    purchase_order_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("purchase_order.id"),
        nullable=False,
        index=True,
    )
    status: Mapped[GoodsReceiptStatus] = mapped_column(
        Enum(GoodsReceiptStatus, values_callable=lambda x: [e.value for e in x]),
        default=GoodsReceiptStatus.DRAFT,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    lines: Mapped[list["GoodsReceiptLine"]] = relationship(
        back_populates="goods_receipt",
        cascade="all, delete-orphan",
    )


class GoodsReceiptLine(Base):
    __tablename__ = "goods_receipt_line"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid_str)
    goods_receipt_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("goods_receipt.id", ondelete="CASCADE"),
        nullable=False,
    )
    purchase_order_line_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("purchase_order_line.id"),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    goods_receipt: Mapped[GoodsReceipt] = relationship(back_populates="lines")
