from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from erp_oms_wms.api import schemas
from erp_oms_wms.api.deps import get_db
from erp_oms_wms.api.rbac import UserRole, get_actor_id, require_roles
from erp_oms_wms.domains.orders.errors import OrderNotFoundError
from erp_oms_wms.domains.returns import service as return_service
from erp_oms_wms.domains.returns.errors import (
    InvalidReturnTransitionError,
    ReturnNotFoundError,
    ReturnOrderNotEligibleError,
)

router = APIRouter(prefix="/returns", tags=["returns"])


@router.post("", response_model=schemas.ReturnRequestOut, status_code=201)
def create_return(
    body: schemas.ReturnCreateIn,
    session: Session = Depends(get_db),
    actor: str = Depends(get_actor_id),
    _role: UserRole = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
) -> schemas.ReturnRequestOut:
    try:
        ret = return_service.create_return(
            session,
            order_id=body.order_id,
            warehouse_id=body.warehouse_id,
            sku=body.sku,
            quantity=body.quantity,
            reason=body.reason,
            actor=actor,
        )
        return schemas.ReturnRequestOut.model_validate(ret)
    except OrderNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ReturnOrderNotEligibleError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{return_id}/accept", response_model=schemas.ReturnRequestOut)
def accept_return(
    return_id: str,
    session: Session = Depends(get_db),
    actor: str = Depends(get_actor_id),
    _role: UserRole = Depends(
        require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.WAREHOUSE_OPERATOR),
    ),
) -> schemas.ReturnRequestOut:
    try:
        ret = return_service.accept_return(session, return_id, actor=actor)
        return schemas.ReturnRequestOut.model_validate(ret)
    except ReturnNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidReturnTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{return_id}/cancel", response_model=schemas.ReturnRequestOut)
def cancel_return(
    return_id: str,
    session: Session = Depends(get_db),
    actor: str = Depends(get_actor_id),
    _role: UserRole = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER)),
) -> schemas.ReturnRequestOut:
    try:
        ret = return_service.cancel_return(session, return_id, actor=actor)
        return schemas.ReturnRequestOut.model_validate(ret)
    except ReturnNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidReturnTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
