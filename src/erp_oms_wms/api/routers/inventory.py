from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from erp_oms_wms.api import schemas
from erp_oms_wms.api.deps import get_db
from erp_oms_wms.api.rbac import UserRole, require_permission
from erp_oms_wms.domains.inventory import service as inventory_service
from erp_oms_wms.domains.inventory.models import InventoryLevel, Reservation, StockMovement

router = APIRouter(prefix="/inventory", tags=["inventory"])


# Возвращает уровень остатка по складу и SKU.
@router.get("/levels", response_model=schemas.InventoryLevelOut)
def get_level(
    warehouse_id: str,
    sku: str,
    session: Session = Depends(get_db),
    _role: UserRole = Depends(require_permission("inventory.read")),
) -> schemas.InventoryLevelOut:
    level = session.scalars(
        select(InventoryLevel).where(
            InventoryLevel.warehouse_id == warehouse_id,
            InventoryLevel.sku == sku,
        ),
    ).first()
    if level is None:
        raise HTTPException(status_code=404, detail="inventory level not found")
    return schemas.InventoryLevelOut(
        warehouse_id=level.warehouse_id,
        sku=level.sku,
        on_hand=level.on_hand,
        reserved=level.reserved,
        available=level.available,
    )


# Приёмка товара (RECEIPT).
@router.get("/movements", response_model=list[schemas.StockMovementOut])
def list_movements(
    warehouse_id: str | None = None,
    sku: str | None = None,
    limit: int = 200,
    session: Session = Depends(get_db),
    _role: UserRole = Depends(require_permission("inventory.read")),
) -> list[schemas.StockMovementOut]:
    stmt = select(StockMovement).order_by(StockMovement.created_at.desc()).limit(limit)
    if warehouse_id:
        stmt = stmt.where(StockMovement.warehouse_id == warehouse_id)
    if sku:
        stmt = stmt.where(StockMovement.sku == sku)
    rows = session.scalars(stmt)
    return [schemas.StockMovementOut.model_validate(r) for r in rows]


@router.get("/reservations", response_model=list[schemas.ReservationOut])
def list_reservations(
    order_id: str | None = None,
    session: Session = Depends(get_db),
    _role: UserRole = Depends(require_permission("inventory.read")),
) -> list[schemas.ReservationOut]:
    stmt = select(Reservation).order_by(Reservation.created_at.desc())
    if order_id:
        stmt = stmt.where(Reservation.order_id == order_id)
    return [schemas.ReservationOut.model_validate(r) for r in session.scalars(stmt)]


@router.post("/receipts", response_model=schemas.InventoryLevelOut)
def post_receipt(
    body: schemas.ReceiptIn,
    session: Session = Depends(get_db),
    _role: UserRole = Depends(require_permission("inventory.adjust")),
) -> schemas.InventoryLevelOut:
    level = inventory_service.apply_receipt(
        session,
        body.warehouse_id,
        body.sku,
        body.quantity,
        "goods_receipt",
        body.reference_id,
    )
    return schemas.InventoryLevelOut(
        warehouse_id=level.warehouse_id,
        sku=level.sku,
        on_hand=level.on_hand,
        reserved=level.reserved,
        available=level.available,
    )
