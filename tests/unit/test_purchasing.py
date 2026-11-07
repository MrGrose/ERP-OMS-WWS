from sqlalchemy import select
from sqlalchemy.orm import Session

import erp_oms_wms.domains.purchasing.service as purchasing_service
from erp_oms_wms.domains.inventory.enums import StockMovementType
from erp_oms_wms.domains.inventory.models import InventoryLevel, StockMovement
from erp_oms_wms.domains.purchasing.enums import GoodsReceiptStatus, PurchaseOrderStatus
from tests.helpers import ensure_supplier


def test_goods_receipt_increases_stock(db_session: Session) -> None:
    ensure_supplier(db_session, "sup-1")
    po = purchasing_service.create_purchase_order(
        db_session,
        supplier_id="sup-1",
        lines=[{"warehouse_id": "wh-1", "sku": "SKU-PO", "quantity_ordered": 20}],
    )
    pol_id = po.lines[0].id
    purchasing_service.confirm_purchase_order(db_session, po.id)
    gr = purchasing_service.create_goods_receipt(
        db_session,
        po.id,
        lines=[{"purchase_order_line_id": pol_id, "quantity": 20}],
    )
    purchasing_service.confirm_goods_receipt(db_session, gr.id)
    db_session.refresh(po)
    assert po.status == PurchaseOrderStatus.RECEIVED
    assert gr.status == GoodsReceiptStatus.CONFIRMED
    level = db_session.scalars(select(InventoryLevel).where(InventoryLevel.sku == "SKU-PO")).one()
    assert level.on_hand == 20
    mv = db_session.scalars(select(StockMovement).where(StockMovement.sku == "SKU-PO")).one()
    assert mv.movement_type == StockMovementType.RECEIPT


def test_partial_receipt_keeps_po_confirmed(db_session: Session) -> None:
    ensure_supplier(db_session, "sup-1")
    po = purchasing_service.create_purchase_order(
        db_session,
        supplier_id="sup-1",
        lines=[{"warehouse_id": "wh-1", "sku": "SKU-P2", "quantity_ordered": 10}],
    )
    pol_id = po.lines[0].id
    purchasing_service.confirm_purchase_order(db_session, po.id)
    gr = purchasing_service.create_goods_receipt(
        db_session,
        po.id,
        lines=[{"purchase_order_line_id": pol_id, "quantity": 4}],
    )
    purchasing_service.confirm_goods_receipt(db_session, gr.id)
    db_session.refresh(po)
    assert po.status == PurchaseOrderStatus.CONFIRMED
    assert po.lines[0].quantity_received == 4
