from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from erp_oms_wms.domains.inventory.models import InventoryLevel, StockMovement
from erp_oms_wms.domains.invoices.enums import InvoiceStatus
from erp_oms_wms.domains.invoices.models import Invoice
from erp_oms_wms.domains.orders.enums import OrderStatus
from erp_oms_wms.domains.orders.models import Order, OrderLine
from erp_oms_wms.domains.purchasing.models import PurchaseOrder, PurchaseOrderLine
from erp_oms_wms.domains.suppliers.models import SupplierProduct


@dataclass(frozen=True)
class StockRow:
    warehouse_id: str
    sku: str
    on_hand: int
    reserved: int
    available: int


def current_stock(session: Session) -> list[StockRow]:
    rows = session.scalars(
        select(InventoryLevel).order_by(InventoryLevel.warehouse_id, InventoryLevel.sku)
    )
    return [
        StockRow(
            warehouse_id=r.warehouse_id,
            sku=r.sku,
            on_hand=r.on_hand,
            reserved=r.reserved,
            available=r.available,
        )
        for r in rows
    ]


def reserved_stock(session: Session) -> list[StockRow]:
    return [r for r in current_stock(session) if r.reserved > 0]


def list_movements(
    session: Session,
    warehouse_id: str | None = None,
    sku: str | None = None,
    limit: int = 500,
) -> list[StockMovement]:
    stmt = select(StockMovement).order_by(StockMovement.created_at.desc()).limit(limit)
    if warehouse_id:
        stmt = stmt.where(StockMovement.warehouse_id == warehouse_id)
    if sku:
        stmt = stmt.where(StockMovement.sku == sku)
    return list(session.scalars(stmt))


def sales_summary(session: Session) -> list[dict[str, object]]:
    stmt = (
        select(
            OrderLine.sku,
            func.sum(OrderLine.quantity_shipped).label("qty"),
            func.sum(OrderLine.quantity_shipped * OrderLine.unit_price_cents).label(
                "revenue_cents"
            ),
        )
        .join(Order, Order.id == OrderLine.order_id)
        .where(Order.status.in_([OrderStatus.SHIPPED, OrderStatus.COMPLETED]))
        .where(OrderLine.unit_price_cents.is_not(None))
        .group_by(OrderLine.sku)
        .order_by(OrderLine.sku)
    )
    return [
        {
            "sku": row.sku,
            "quantity_shipped": int(row.qty or 0),
            "revenue_cents": int(row.revenue_cents or 0),
        }
        for row in session.execute(stmt)
    ]


def purchases_summary(session: Session) -> list[dict[str, object]]:
    stmt = (
        select(
            PurchaseOrderLine.sku,
            func.sum(PurchaseOrderLine.quantity_received).label("qty"),
        )
        .group_by(PurchaseOrderLine.sku)
        .order_by(PurchaseOrderLine.sku)
    )
    return [
        {"sku": row.sku, "quantity_received": int(row.qty or 0)} for row in session.execute(stmt)
    ]


def unpaid_invoices(session: Session) -> list[Invoice]:
    stmt = (
        select(Invoice)
        .where(Invoice.status == InvoiceStatus.PENDING_PAYMENT)
        .order_by(Invoice.created_at)
    )
    return list(session.scalars(stmt))


def supplier_balances(session: Session) -> list[dict[str, object]]:
    stmt = (
        select(
            PurchaseOrder.supplier_id,
            func.count(func.distinct(PurchaseOrder.id)).label("po_count"),
            func.coalesce(func.sum(PurchaseOrderLine.quantity_received), 0).label("units_received"),
        )
        .join(PurchaseOrderLine, PurchaseOrderLine.purchase_order_id == PurchaseOrder.id)
        .group_by(PurchaseOrder.supplier_id)
    )
    return [
        {
            "supplier_id": row.supplier_id,
            "purchase_order_count": int(row.po_count),
            "units_received": int(row.units_received),
        }
        for row in session.execute(stmt)
    ]


def stock_turnover(session: Session, *, since: datetime | None = None) -> list[dict[str, object]]:
    stmt = select(
        StockMovement.warehouse_id,
        StockMovement.sku,
        func.sum(func.abs(StockMovement.on_hand_delta)).label("magnitude"),
    ).group_by(StockMovement.warehouse_id, StockMovement.sku)
    if since is not None:
        stmt = stmt.where(StockMovement.created_at >= since)
    return [
        {
            "warehouse_id": row.warehouse_id,
            "sku": row.sku,
            "movement_magnitude": int(row.magnitude or 0),
        }
        for row in session.execute(stmt)
    ]


def estimated_supplier_spend(session: Session) -> list[dict[str, object]]:
    stmt = (
        select(
            SupplierProduct.supplier_id,
            func.sum(SupplierProduct.purchase_price_cents).label("listed_prices_cents"),
            func.count(SupplierProduct.id).label("sku_count"),
        )
        .where(SupplierProduct.is_active.is_(True))
        .group_by(SupplierProduct.supplier_id)
    )
    return [
        {
            "supplier_id": row.supplier_id,
            "active_sku_count": int(row.sku_count),
            "sum_list_prices_cents": int(row.listed_prices_cents or 0),
        }
        for row in session.execute(stmt)
    ]
