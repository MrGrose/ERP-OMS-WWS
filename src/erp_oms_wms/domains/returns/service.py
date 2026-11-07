from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from erp_oms_wms.domains.audit import service as audit_service
from erp_oms_wms.domains.inventory import service as inventory_service
from erp_oms_wms.domains.orders.enums import OrderStatus
from erp_oms_wms.domains.orders.errors import OrderNotFoundError
from erp_oms_wms.domains.orders.models import Order, OrderLine
from erp_oms_wms.domains.returns.enums import ReturnStatus
from erp_oms_wms.domains.returns.errors import (
    InvalidReturnTransitionError,
    ReturnNotFoundError,
    ReturnOrderNotEligibleError,
)
from erp_oms_wms.domains.returns.models import ReturnRequest

_ELIGIBLE_ORDER_STATUSES = frozenset({OrderStatus.SHIPPED, OrderStatus.COMPLETED})


def _load_order(session: Session, order_id: str) -> Order:
    order = session.scalars(select(Order).where(Order.id == order_id)).first()
    if order is None:
        raise OrderNotFoundError(order_id)
    return order


def create_return(
    session: Session,
    *,
    order_id: str,
    warehouse_id: str,
    sku: str,
    quantity: int,
    reason: str | None,
    actor: str,
) -> ReturnRequest:
    if quantity <= 0:
        raise ValueError("quantity must be positive")
    order = _load_order(session, order_id)
    if order.status not in _ELIGIBLE_ORDER_STATUSES:
        raise ReturnOrderNotEligibleError(order_id, order.status.value)
    line = session.scalars(
        select(OrderLine).where(
            OrderLine.order_id == order_id,
            OrderLine.warehouse_id == warehouse_id,
            OrderLine.sku == sku,
        ),
    ).first()
    if line is None or quantity > line.quantity:
        raise ValueError("return quantity exceeds order line")
    ret = ReturnRequest(
        order_id=order_id,
        warehouse_id=warehouse_id,
        sku=sku,
        quantity=quantity,
        reason=reason,
        status=ReturnStatus.INITIATED,
    )
    session.add(ret)
    session.flush()
    audit_service.record(
        session,
        actor=actor,
        action="return.initiated",
        entity_type="return_request",
        entity_id=ret.id,
        details=order_id,
    )
    return ret


def accept_return(session: Session, return_id: str, *, actor: str) -> ReturnRequest:
    ret = session.get(ReturnRequest, return_id)
    if ret is None:
        raise ReturnNotFoundError(return_id)
    if ret.status != ReturnStatus.INITIATED:
        raise InvalidReturnTransitionError(f"return {return_id} status {ret.status.value}")
    inventory_service.apply_return(
        session,
        warehouse_id=ret.warehouse_id,
        sku=ret.sku,
        quantity=ret.quantity,
        reference_type="return_request",
        reference_id=ret.id,
        reason=ret.reason,
    )
    ret.status = ReturnStatus.ACCEPTED
    ret.accepted_at = datetime.now(UTC)
    session.flush()
    audit_service.record(
        session,
        actor=actor,
        action="return.accepted",
        entity_type="return_request",
        entity_id=ret.id,
    )
    return ret


def cancel_return(session: Session, return_id: str, *, actor: str) -> ReturnRequest:
    ret = session.get(ReturnRequest, return_id)
    if ret is None:
        raise ReturnNotFoundError(return_id)
    if ret.status != ReturnStatus.INITIATED:
        raise InvalidReturnTransitionError(f"return {return_id} status {ret.status.value}")
    ret.status = ReturnStatus.CANCELLED
    session.flush()
    audit_service.record(
        session,
        actor=actor,
        action="return.cancelled",
        entity_type="return_request",
        entity_id=ret.id,
    )
    return ret
