from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from erp_oms_wms.api import schemas
from erp_oms_wms.api.deps import get_db
from erp_oms_wms.api.rbac import UserRole, get_actor_id, require_roles
from erp_oms_wms.domains.inventory.errors import InsufficientAvailableError
from erp_oms_wms.domains.transfers import service as transfer_service
from erp_oms_wms.domains.transfers.errors import (
    InvalidTransferTransitionError,
    TransferNotFoundError,
)

router = APIRouter(prefix="/transfers", tags=["transfers"])


@router.post("", response_model=schemas.WarehouseTransferOut, status_code=201)
def create_transfer(
    body: schemas.WarehouseTransferCreateIn,
    session: Session = Depends(get_db),
    actor: str = Depends(get_actor_id),
    _role: UserRole = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.WAREHOUSE_OPERATOR),
    ),
) -> schemas.WarehouseTransferOut:
    try:
        transfer = transfer_service.create_transfer(
            session,
            from_warehouse_id=body.from_warehouse_id,
            to_warehouse_id=body.to_warehouse_id,
            sku=body.sku,
            quantity=body.quantity,
            actor=actor,
        )
        return schemas.WarehouseTransferOut.model_validate(transfer)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{transfer_id}/complete", response_model=schemas.WarehouseTransferOut)
def complete_transfer(
    transfer_id: str,
    session: Session = Depends(get_db),
    actor: str = Depends(get_actor_id),
    _role: UserRole = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.WAREHOUSE_OPERATOR),
    ),
) -> schemas.WarehouseTransferOut:
    try:
        transfer = transfer_service.complete_transfer(session, transfer_id, actor=actor)
        return schemas.WarehouseTransferOut.model_validate(transfer)
    except TransferNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (InvalidTransferTransitionError, InsufficientAvailableError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{transfer_id}/cancel", response_model=schemas.WarehouseTransferOut)
def cancel_transfer(
    transfer_id: str,
    session: Session = Depends(get_db),
    actor: str = Depends(get_actor_id),
    _role: UserRole = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
) -> schemas.WarehouseTransferOut:
    try:
        transfer = transfer_service.cancel_transfer(session, transfer_id, actor=actor)
        return schemas.WarehouseTransferOut.model_validate(transfer)
    except TransferNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidTransferTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
