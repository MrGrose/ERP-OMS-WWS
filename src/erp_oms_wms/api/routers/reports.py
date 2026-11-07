from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from erp_oms_wms.api import schemas
from erp_oms_wms.api.deps import get_db
from erp_oms_wms.api.rbac import UserRole, require_permission
from erp_oms_wms.domains.invoices.models import Invoice
from erp_oms_wms.domains.reporting import service as reporting_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/stock", response_model=list[schemas.StockReportRow])
def report_stock(
    session: Session = Depends(get_db),
    _role: UserRole = Depends(require_permission("inventory.read")),
) -> list[schemas.StockReportRow]:
    return [
        schemas.StockReportRow.model_validate(r.__dict__)
        for r in reporting_service.current_stock(session)
    ]


@router.get("/stock/reserved", response_model=list[schemas.StockReportRow])
def report_reserved_stock(
    session: Session = Depends(get_db),
    _role: UserRole = Depends(require_permission("inventory.read")),
) -> list[schemas.StockReportRow]:
    return [
        schemas.StockReportRow.model_validate(r.__dict__)
        for r in reporting_service.reserved_stock(session)
    ]


@router.get("/movements", response_model=list[schemas.StockMovementOut])
def report_movements(
    warehouse_id: str | None = None,
    sku: str | None = None,
    session: Session = Depends(get_db),
    _role: UserRole = Depends(require_permission("inventory.read")),
) -> list[schemas.StockMovementOut]:
    rows = reporting_service.list_movements(session, warehouse_id=warehouse_id, sku=sku)
    return [schemas.StockMovementOut.model_validate(r) for r in rows]


@router.get("/sales")
def report_sales(
    session: Session = Depends(get_db),
    _role: UserRole = Depends(require_permission("finance.read")),
) -> list[dict[str, object]]:
    return reporting_service.sales_summary(session)


@router.get("/purchases")
def report_purchases(
    session: Session = Depends(get_db),
    _role: UserRole = Depends(require_permission("finance.read")),
) -> list[dict[str, object]]:
    return reporting_service.purchases_summary(session)


@router.get("/invoices/unpaid")
def report_unpaid_invoices(
    session: Session = Depends(get_db),
    _role: UserRole = Depends(require_permission("finance.read")),
) -> list[dict[str, object]]:
    rows: list[Invoice] = reporting_service.unpaid_invoices(session)
    return [
        {
            "id": inv.id,
            "order_id": inv.order_id,
            "amount_cents": inv.amount_cents,
            "currency": inv.currency,
            "status": inv.status.value,
        }
        for inv in rows
    ]


@router.get("/suppliers/balances")
def report_supplier_balances(
    session: Session = Depends(get_db),
    _role: UserRole = Depends(require_permission("finance.read")),
) -> list[dict[str, object]]:
    return reporting_service.supplier_balances(session)


@router.get("/stock/turnover")
def report_stock_turnover(
    session: Session = Depends(get_db),
    _role: UserRole = Depends(require_permission("inventory.read")),
) -> list[dict[str, object]]:
    return reporting_service.stock_turnover(session)
