from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from erp_oms_wms.api import schemas
from erp_oms_wms.api.deps import get_db
from erp_oms_wms.api.rbac import UserRole, require_permission
from erp_oms_wms.domains.purchasing import service as purchasing_service
from erp_oms_wms.domains.purchasing.errors import InvalidPurchasingTransitionError, PurchasingError

router = APIRouter(prefix="/purchasing", tags=["purchasing"])


@router.post("/purchase-orders", response_model=schemas.PurchaseOrderOut, status_code=201)
def create_po(
    body: schemas.PurchaseOrderCreateIn,
    session: Session = Depends(get_db),
    _role: UserRole = Depends(require_permission("orders.manage")),
) -> schemas.PurchaseOrderOut:
    po = purchasing_service.create_purchase_order(
        session,
        supplier_id=body.supplier_id,
        lines=[line.model_dump() for line in body.lines],
    )
    session.refresh(po)
    return schemas.PurchaseOrderOut.model_validate(po)


@router.post("/purchase-orders/{po_id}/confirm", response_model=schemas.PurchaseOrderOut)
def confirm_po(
    po_id: str,
    session: Session = Depends(get_db),
    _role: UserRole = Depends(require_permission("orders.manage")),
) -> schemas.PurchaseOrderOut:
    try:
        po = purchasing_service.confirm_purchase_order(session, po_id)
        session.refresh(po)
        return schemas.PurchaseOrderOut.model_validate(po)
    except InvalidPurchasingTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/goods-receipts", response_model=schemas.GoodsReceiptOut, status_code=201)
def create_gr(
    body: schemas.GoodsReceiptCreateIn,
    session: Session = Depends(get_db),
    _role: UserRole = Depends(require_permission("inventory.adjust")),
) -> schemas.GoodsReceiptOut:
    try:
        gr = purchasing_service.create_goods_receipt(
            session,
            body.purchase_order_id,
            lines=[line.model_dump() for line in body.lines],
        )
        session.refresh(gr)
        return schemas.GoodsReceiptOut.model_validate(gr)
    except PurchasingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/goods-receipts/{gr_id}/confirm", response_model=schemas.GoodsReceiptOut)
def confirm_gr(
    gr_id: str,
    session: Session = Depends(get_db),
    _role: UserRole = Depends(require_permission("inventory.adjust")),
) -> schemas.GoodsReceiptOut:
    try:
        gr = purchasing_service.confirm_goods_receipt(session, gr_id)
        session.refresh(gr)
        return schemas.GoodsReceiptOut.model_validate(gr)
    except InvalidPurchasingTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except PurchasingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
