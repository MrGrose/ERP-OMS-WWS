import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from erp_oms_wms.db import Base


def new_uuid_str() -> str:
    return str(uuid.uuid4())


class Supplier(Base):
    __tablename__ = "supplier"
    __table_args__ = (UniqueConstraint("code", name="uq_supplier_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid_str)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SupplierProduct(Base):
    __tablename__ = "supplier_product"
    __table_args__ = (
        UniqueConstraint("supplier_id", "sku", name="uq_supplier_product_sku"),
        CheckConstraint("purchase_price_cents >= 0", name="ck_supplier_price_nonneg"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid_str)
    supplier_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("supplier.id", ondelete="CASCADE"),
        nullable=False,
    )
    sku: Mapped[str] = mapped_column(String(128), nullable=False)
    supplier_sku: Mapped[str] = mapped_column(String(128), nullable=False)
    purchase_price_cents: Mapped[int] = mapped_column(nullable=False)
    lead_time_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
