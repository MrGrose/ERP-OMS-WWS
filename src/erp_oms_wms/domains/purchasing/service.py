from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from erp_oms_wms.domains.inventory import service as inventory_service
from erp_oms_wms.domains.purchasing.enums import GoodsReceiptStatus, PurchaseOrderStatus
from erp_oms_wms.domains.purchasing.errors import (
    GoodsReceiptNotFoundError,
    InvalidPurchasingTransitionError,
    PurchaseOrderNotFoundError,
)
from erp_oms_wms.domains.purchasing.models import (
    GoodsReceipt,
    GoodsReceiptLine,
    PurchaseOrder,
    PurchaseOrderLine,
)
from erp_oms_wms.domains.purchasing.transitions import (
    assert_gr_transition,
    assert_po_transition,
)
from erp_oms_wms.domains.suppliers.errors import SupplierNotFoundError
from erp_oms_wms.domains.suppliers.models import Supplier


def _positive_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field} must be a positive integer")
    return value


# Создает закупку в DRAFT.
def create_purchase_order(
    session: Session,
    supplier_id: str,
    lines: list[dict[str, object]],
) -> PurchaseOrder:
    if session.get(Supplier, supplier_id) is None:
        raise SupplierNotFoundError(supplier_id)
    po = PurchaseOrder(supplier_id=supplier_id)
    session.add(po)
    session.flush()
    for raw in lines:
        qty = _positive_int(raw["quantity_ordered"], "quantity_ordered")
        if qty <= 0:
            raise ValueError("quantity_ordered must be positive")
        session.add(
            PurchaseOrderLine(
                purchase_order_id=po.id,
                warehouse_id=str(raw["warehouse_id"]),
                sku=str(raw["sku"]),
                quantity_ordered=qty,
            ),
        )
    session.flush()
    return po


def confirm_purchase_order(session: Session, purchase_order_id: str) -> PurchaseOrder:
    po = _load_po(session, purchase_order_id)
    assert_po_transition(po.status, PurchaseOrderStatus.CONFIRMED)
    po.status = PurchaseOrderStatus.CONFIRMED
    session.flush()
    return po


# Создает приемку по строкам ПО (DRAFT).
def create_goods_receipt(
    session: Session,
    purchase_order_id: str,
    lines: list[dict[str, object]],
) -> GoodsReceipt:
    po = _load_po(session, purchase_order_id)
    if po.status != PurchaseOrderStatus.CONFIRMED:
        raise InvalidPurchasingTransitionError("Приёмка только для CONFIRMED PO")
    gr = GoodsReceipt(purchase_order_id=po.id)
    session.add(gr)
    session.flush()
    po_lines = {line.id: line for line in po.lines}
    for raw in lines:
        line_id = str(raw["purchase_order_line_id"])
        qty = _positive_int(raw["quantity"], "quantity")
        if qty <= 0:
            raise ValueError("quantity must be positive")
        pol = po_lines.get(line_id)
        if pol is None:
            raise PurchaseOrderNotFoundError(line_id)
        remaining = pol.quantity_ordered - pol.quantity_received
        if qty > remaining:
            raise InvalidPurchasingTransitionError(f"Превышение остатка по строке {line_id}")
        session.add(
            GoodsReceiptLine(
                goods_receipt_id=gr.id,
                purchase_order_line_id=line_id,
                quantity=qty,
            ),
        )
    session.flush()
    return gr


# Подтверждает приемку: StockMovement RECEIPT, обновление PO.
def confirm_goods_receipt(session: Session, goods_receipt_id: str) -> GoodsReceipt:
    gr = _load_gr(session, goods_receipt_id)
    assert_gr_transition(gr.status, GoodsReceiptStatus.CONFIRMED)
    po = _load_po(session, gr.purchase_order_id)
    for gr_line in gr.lines:
        pol = session.get(PurchaseOrderLine, gr_line.purchase_order_line_id)
        if pol is None:
            raise PurchaseOrderNotFoundError(gr_line.purchase_order_line_id)
        inventory_service.apply_receipt(
            session,
            pol.warehouse_id,
            pol.sku,
            gr_line.quantity,
            "goods_receipt",
            gr.id,
        )
        pol.quantity_received += gr_line.quantity
    gr.status = GoodsReceiptStatus.CONFIRMED
    if all(line.quantity_received >= line.quantity_ordered for line in po.lines):
        assert_po_transition(po.status, PurchaseOrderStatus.RECEIVED)
        po.status = PurchaseOrderStatus.RECEIVED
    session.flush()
    return gr


def _load_po(session: Session, purchase_order_id: str) -> PurchaseOrder:
    po = (
        session.scalars(
            select(PurchaseOrder)
            .options(joinedload(PurchaseOrder.lines))
            .where(PurchaseOrder.id == purchase_order_id),
        )
        .unique()
        .first()
    )
    if po is None:
        raise PurchaseOrderNotFoundError(purchase_order_id)
    return po


def _load_gr(session: Session, goods_receipt_id: str) -> GoodsReceipt:
    gr = (
        session.scalars(
            select(GoodsReceipt)
            .options(joinedload(GoodsReceipt.lines))
            .where(GoodsReceipt.id == goods_receipt_id),
        )
        .unique()
        .first()
    )
    if gr is None:
        raise GoodsReceiptNotFoundError(goods_receipt_id)
    return gr
