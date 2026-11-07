from sqlalchemy import select
from sqlalchemy.orm import Session

import erp_oms_wms.domains.returns.service as return_service
import erp_oms_wms.domains.transfers.service as transfer_service
from erp_oms_wms.domains.inventory import service as inventory_service
from erp_oms_wms.domains.inventory.enums import StockMovementType
from erp_oms_wms.domains.inventory.models import InventoryLevel, StockMovement
from erp_oms_wms.domains.orders.enums import OrderStatus
from erp_oms_wms.domains.orders.models import Order, OrderLine
from erp_oms_wms.domains.returns.enums import ReturnStatus
from erp_oms_wms.domains.transfers.enums import WarehouseTransferStatus


def test_transfer_moves_available_between_warehouses(db_session: Session) -> None:
    inventory_service.ensure_inventory_level(db_session, "wh-a", "SKU-1", initial_on_hand=20)
    transfer = transfer_service.create_transfer(
        db_session,
        from_warehouse_id="wh-a",
        to_warehouse_id="wh-b",
        sku="SKU-1",
        quantity=8,
        actor="tester",
    )
    transfer_service.complete_transfer(db_session, transfer.id, actor="tester")
    level_a = db_session.scalars(
        select(InventoryLevel).where(
            InventoryLevel.warehouse_id == "wh-a",
            InventoryLevel.sku == "SKU-1",
        ),
    ).one()
    level_b = db_session.scalars(
        select(InventoryLevel).where(
            InventoryLevel.warehouse_id == "wh-b",
            InventoryLevel.sku == "SKU-1",
        ),
    ).one()
    assert level_a.on_hand == 12
    assert level_b.on_hand == 8
    movements = list(
        db_session.scalars(
            select(StockMovement).where(StockMovement.reference_id == transfer.id),
        ),
    )
    assert len(movements) == 2
    assert {m.movement_type for m in movements} == {StockMovementType.TRANSFER}
    db_session.refresh(transfer)
    assert transfer.status == WarehouseTransferStatus.COMPLETED


def test_return_accept_increases_on_hand(db_session: Session) -> None:
    inventory_service.ensure_inventory_level(db_session, "wh-1", "SKU-2", initial_on_hand=0)
    order = Order(customer_id="c1", status=OrderStatus.SHIPPED)
    db_session.add(order)
    db_session.flush()
    db_session.add(
        OrderLine(
            order_id=order.id,
            warehouse_id="wh-1",
            sku="SKU-2",
            quantity=5,
        ),
    )
    db_session.flush()
    ret = return_service.create_return(
        db_session,
        order_id=order.id,
        warehouse_id="wh-1",
        sku="SKU-2",
        quantity=2,
        reason="defect",
        actor="mgr",
    )
    return_service.accept_return(db_session, ret.id, actor="wh")
    level = db_session.scalars(
        select(InventoryLevel).where(
            InventoryLevel.warehouse_id == "wh-1",
            InventoryLevel.sku == "SKU-2",
        ),
    ).one()
    assert level.on_hand == 2
    db_session.refresh(ret)
    assert ret.status == ReturnStatus.ACCEPTED
