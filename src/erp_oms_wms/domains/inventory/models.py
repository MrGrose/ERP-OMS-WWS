import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from erp_oms_wms.db import Base
from erp_oms_wms.domains.inventory.enums import ReservationStatus, StockMovementType


def new_uuid_str() -> str:
    return str(uuid.uuid4())


class InventoryLevel(Base):
    __tablename__ = "inventory_level"
    __table_args__ = (
        UniqueConstraint("warehouse_id", "sku", name="uq_inventory_level_wh_sku"),
        CheckConstraint("on_hand >= 0", name="ck_inventory_on_hand_nonneg"),
        CheckConstraint("reserved >= 0", name="ck_inventory_reserved_nonneg"),
        CheckConstraint("reserved <= on_hand", name="ck_inventory_reserved_le_on_hand"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid_str)
    warehouse_id: Mapped[str] = mapped_column(String(64), nullable=False)
    sku: Mapped[str] = mapped_column(String(128), nullable=False)
    on_hand: Mapped[int] = mapped_column(nullable=False, default=0)
    reserved: Mapped[int] = mapped_column(nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    @property
    def available(self) -> int:
        return self.on_hand - self.reserved


class StockMovement(Base):
    __tablename__ = "stock_movement"
    __table_args__ = (Index("ix_stock_movement_wh_sku", "warehouse_id", "sku"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid_str)
    movement_type: Mapped[StockMovementType] = mapped_column(
        Enum(StockMovementType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    warehouse_id: Mapped[str] = mapped_column(String(64), nullable=False)
    sku: Mapped[str] = mapped_column(String(128), nullable=False)
    on_hand_delta: Mapped[int] = mapped_column(nullable=False, default=0)
    reserved_delta: Mapped[int] = mapped_column(nullable=False, default=0)
    reference_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reference_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Reservation(Base):
    __tablename__ = "reservation"
    __table_args__ = (Index("ix_reservation_order", "order_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid_str)
    order_id: Mapped[str] = mapped_column(String(128), nullable=False)
    warehouse_id: Mapped[str] = mapped_column(String(64), nullable=False)
    sku: Mapped[str] = mapped_column(String(128), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[ReservationStatus] = mapped_column(
        Enum(ReservationStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ReservationStatus.ACTIVE,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
