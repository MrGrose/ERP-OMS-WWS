import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from erp_oms_wms.domains.inventory import service
from erp_oms_wms.domains.inventory.enums import ReservationStatus, StockMovementType
from erp_oms_wms.domains.inventory.errors import InsufficientAvailableError
from erp_oms_wms.domains.inventory.models import InventoryLevel, StockMovement


def test_available_is_on_hand_minus_reserved(db_session: Session) -> None:
    level = service.ensure_inventory_level(db_session, "wh-1", "SKU-1", initial_on_hand=100)
    level.reserved = 20
    db_session.flush()
    assert level.available == 80


def test_reserve_rejects_when_insufficient(db_session: Session) -> None:
    service.ensure_inventory_level(db_session, "wh-1", "SKU-1", initial_on_hand=5)
    with pytest.raises(InsufficientAvailableError):
        service.reserve_for_order(
            db_session,
            order_id="ord-1",
            warehouse_id="wh-1",
            sku="SKU-1",
            quantity=10,
        )


def test_reserve_and_release_restores_available(db_session: Session) -> None:
    service.ensure_inventory_level(db_session, "wh-1", "SKU-1", initial_on_hand=10)
    res = service.reserve_for_order(
        db_session,
        order_id="ord-1",
        warehouse_id="wh-1",
        sku="SKU-1",
        quantity=3,
    )
    level = db_session.scalars(
        select(InventoryLevel).where(
            InventoryLevel.warehouse_id == "wh-1",
            InventoryLevel.sku == "SKU-1",
        ),
    ).one()
    assert level.on_hand == 10
    assert level.reserved == 3
    assert level.available == 7
    service.release_reservation(db_session, res.id)
    db_session.refresh(level)
    assert level.reserved == 0
    assert res.status == ReservationStatus.RELEASED


def test_shipment_reduces_on_hand_and_reserved(db_session: Session) -> None:
    service.ensure_inventory_level(db_session, "wh-1", "SKU-1", initial_on_hand=10)
    res = service.reserve_for_order(
        db_session,
        order_id="ord-2",
        warehouse_id="wh-1",
        sku="SKU-1",
        quantity=4,
    )
    service.ship_reservation(db_session, res.id)
    level = db_session.scalars(select(InventoryLevel).where(InventoryLevel.sku == "SKU-1")).one()
    assert level.on_hand == 6
    assert level.reserved == 0
    movements = list(
        db_session.scalars(select(StockMovement).order_by(StockMovement.created_at)),
    )
    types = [m.movement_type for m in movements]
    assert StockMovementType.RESERVATION in types
    assert StockMovementType.SHIPMENT in types


def test_receipt_increments_on_hand_with_movement(db_session: Session) -> None:
    service.apply_receipt(db_session, "wh-1", "SKU-2", 50, "goods_receipt", "gr-1")
    level = db_session.scalars(select(InventoryLevel).where(InventoryLevel.sku == "SKU-2")).one()
    assert level.on_hand == 50
    mv = db_session.scalars(select(StockMovement)).one()
    assert mv.movement_type == StockMovementType.RECEIPT
    assert mv.on_hand_delta == 50
