from collections.abc import Callable

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from erp_oms_wms.api import schemas
from erp_oms_wms.api.deps import get_db
from erp_oms_wms.api.rbac import UserRole, require_permission
from erp_oms_wms.domains.orders import service as order_service
from erp_oms_wms.domains.orders.errors import (
    InvalidOrderTransitionError,
    OrderError,
    OrderNotFoundError,
)
from erp_oms_wms.domains.orders.models import Order

router = APIRouter(prefix="/orders", tags=["orders"])


# Создаёт заказ в статусе DRAFT.
@router.post("", response_model=schemas.OrderOut, status_code=201)
def create_order(
    body: schemas.OrderCreateIn,
    session: Session = Depends(get_db),
    _role: UserRole = Depends(require_permission("orders.manage")),
) -> schemas.OrderOut:
    order = order_service.create_draft_order(
        session,
        customer_id=body.customer_id,
        lines=[line.model_dump() for line in body.lines],
    )
    session.refresh(order)
    return schemas.OrderOut.model_validate(order)


# Подтверждает заказ (DRAFT → CONFIRMED).
@router.post("/{order_id}/confirm", response_model=schemas.OrderOut)
def confirm_order(
    order_id: str,
    session: Session = Depends(get_db),
    _role: UserRole = Depends(require_permission("orders.manage")),
) -> schemas.OrderOut:
    return _run_order_action(session, order_id, order_service.confirm_order)


# Резервирует остатки (CONFIRMED → RESERVED).
@router.post("/{order_id}/reserve", response_model=schemas.OrderOut)
def reserve_order(
    order_id: str,
    session: Session = Depends(get_db),
    _role: UserRole = Depends(require_permission("orders.manage")),
) -> schemas.OrderOut:
    return _run_order_action(session, order_id, order_service.reserve_order)


# Отменяет заказ и снимает резервы.
@router.post("/{order_id}/cancel", response_model=schemas.OrderOut)
def cancel_order(
    order_id: str,
    session: Session = Depends(get_db),
    _role: UserRole = Depends(require_permission("orders.manage")),
) -> schemas.OrderOut:
    return _run_order_action(session, order_id, order_service.cancel_order)


# Перевод в сборку (→ ASSEMBLING).
@router.post("/{order_id}/assemble", response_model=schemas.OrderOut)
def assemble_order(
    order_id: str,
    session: Session = Depends(get_db),
    _role: UserRole = Depends(require_permission("orders.manage")),
) -> schemas.OrderOut:
    return _run_order_action(session, order_id, order_service.start_assembling)


# Отгрузка (ASSEMBLING → SHIPPED).
@router.post("/{order_id}/ship", response_model=schemas.OrderOut)
def ship_order(
    order_id: str,
    session: Session = Depends(get_db),
    _role: UserRole = Depends(require_permission("orders.manage")),
) -> schemas.OrderOut:
    return _run_order_action(session, order_id, order_service.ship_order)


@router.post("/{order_id}/lines/{line_id}/ship", response_model=schemas.OrderOut)
def ship_order_line(
    order_id: str,
    line_id: str,
    body: schemas.OrderLineShipIn,
    session: Session = Depends(get_db),
    _role: UserRole = Depends(require_permission("orders.manage")),
) -> schemas.OrderOut:
    try:
        order = order_service.ship_order_line(session, order_id, line_id, body.quantity)
        session.refresh(order)
        return schemas.OrderOut.model_validate(order)
    except OrderNotFoundError:
        raise HTTPException(status_code=404, detail="order not found") from None
    except InvalidOrderTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{order_id}/complete", response_model=schemas.OrderOut)
def complete_order(
    order_id: str,
    session: Session = Depends(get_db),
    _role: UserRole = Depends(require_permission("orders.manage")),
) -> schemas.OrderOut:
    return _run_order_action(session, order_id, order_service.complete_order)


def _run_order_action(
    session: Session,
    order_id: str,
    fn: Callable[[Session, str], Order],
) -> schemas.OrderOut:
    try:
        order = fn(session, order_id)
        session.refresh(order)
        return schemas.OrderOut.model_validate(order)
    except OrderNotFoundError:
        raise HTTPException(status_code=404, detail="order not found") from None
    except InvalidOrderTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except OrderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
