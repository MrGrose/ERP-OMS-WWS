from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from erp_oms_wms.api import schemas
from erp_oms_wms.api.deps import get_db
from erp_oms_wms.api.rbac import UserRole, require_roles
from erp_oms_wms.domains.warehouses import service as warehouse_service
from erp_oms_wms.domains.warehouses.errors import WarehouseNotFoundError

router = APIRouter(prefix="/warehouses", tags=["warehouses"])


@router.get("", response_model=list[schemas.WarehouseOut])
def list_warehouses(session: Session = Depends(get_db)) -> list[schemas.WarehouseOut]:
    return [
        schemas.WarehouseOut.model_validate(w) for w in warehouse_service.list_warehouses(session)
    ]


@router.post("", response_model=schemas.WarehouseOut, status_code=201)
def create_warehouse(
    body: schemas.WarehouseCreateIn,
    session: Session = Depends(get_db),
    _role: UserRole = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
) -> schemas.WarehouseOut:
    try:
        wh = warehouse_service.create_warehouse(session, warehouse_id=body.id, name=body.name)
        return schemas.WarehouseOut.model_validate(wh)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{warehouse_id}", response_model=schemas.WarehouseOut)
def get_warehouse(warehouse_id: str, session: Session = Depends(get_db)) -> schemas.WarehouseOut:
    try:
        return schemas.WarehouseOut.model_validate(
            warehouse_service.get_warehouse(session, warehouse_id)
        )
    except WarehouseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
