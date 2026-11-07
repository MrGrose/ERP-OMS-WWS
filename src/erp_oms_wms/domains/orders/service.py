from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from erp_oms_wms.domains.customers.errors import CustomerInactiveError, CustomerNotFoundError
from erp_oms_wms.domains.inventory import service as inventory_service
from erp_oms_wms.domains.inventory.errors import InsufficientAvailableError
from erp_oms_wms.domains.inventory.models import Reservation
from erp_oms_wms.domains.orders.enums import OrderStatus
from erp_oms_wms.domains.orders.errors import InvalidOrderTransitionError, OrderNotFoundError
from erp_oms_wms.domains.orders.models import Order, OrderLine
from erp_oms_wms.domains.orders.transitions import assert_transition
from erp_oms_wms.domains.pricing import service as pricing_service
from erp_oms_wms.domains.pricing.errors import PriceNotFoundError


def _positive_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field} must be a positive integer")
    return value


# Создаёт заказ в статусе DRAFT с позициями.
def create_draft_order(
    session: Session,
    *,
    customer_id: str | None,
    lines: list[dict[str, object]],
) -> Order:
    order = Order(customer_id=customer_id, status=OrderStatus.DRAFT)
    session.add(order)
    session.flush()
    for raw in lines:
        line = OrderLine(
            order_id=order.id,
            warehouse_id=str(raw["warehouse_id"]),
            sku=str(raw["sku"]),
            quantity=_positive_int(raw["quantity"], "quantity"),
        )
        if line.quantity <= 0:
            raise ValueError("quantity must be positive")
        session.add(line)
    session.flush()
    return order


def compute_order_total_cents(order: Order) -> int:
    total = 0
    for line in order.lines:
        if line.unit_price_cents is None:
            raise InvalidOrderTransitionError(f"line {line.id} missing unit_price_cents")
        total += line.quantity * line.unit_price_cents
    return total


# Переводит DRAFT → CONFIRMED без резерва.
def confirm_order(session: Session, order_id: str) -> Order:
    order = _load_order(session, order_id)
    assert_transition(order.status, OrderStatus.CONFIRMED)
    for line in order.lines:
        try:
            line.unit_price_cents = pricing_service.resolve_unit_price_cents(
                session,
                sku=line.sku,
                customer_id=order.customer_id,
            )
        except (PriceNotFoundError, CustomerNotFoundError, CustomerInactiveError) as exc:
            raise InvalidOrderTransitionError(str(exc)) from exc
    order.status = OrderStatus.CONFIRMED
    session.flush()
    return order


# Резервирует все позиции и переводит CONFIRMED → RESERVED.
def reserve_order(session: Session, order_id: str) -> Order:
    order = _load_order(session, order_id)
    assert_transition(order.status, OrderStatus.RESERVED)
    try:
        for line in order.lines:
            reservation = inventory_service.reserve_for_order(
                session,
                order_id=order.id,
                warehouse_id=line.warehouse_id,
                sku=line.sku,
                quantity=line.quantity,
            )
            line.reservation_id = reservation.id
    except InsufficientAvailableError as exc:
        raise InvalidOrderTransitionError(str(exc)) from exc
    order.status = OrderStatus.RESERVED
    session.flush()
    return order


# Освобождает резервы и отменяет заказ.
def cancel_order(session: Session, order_id: str) -> Order:
    order = _load_order(session, order_id)
    assert_transition(order.status, OrderStatus.CANCELLED)
    for line in order.lines:
        if line.reservation_id:
            inventory_service.release_reservation(session, line.reservation_id)
            line.reservation_id = None
    order.status = OrderStatus.CANCELLED
    session.flush()
    return order


# Перевод RESERVED/PAID → ASSEMBLING (без изменения остатков).
def start_assembling(session: Session, order_id: str) -> Order:
    order = _load_order(session, order_id)
    assert_transition(order.status, OrderStatus.ASSEMBLING)
    order.status = OrderStatus.ASSEMBLING
    session.flush()
    return order


def _ship_line_quantity(session: Session, order: Order, line: OrderLine, quantity: int) -> None:
    remaining = line.quantity - line.quantity_shipped
    if quantity <= 0 or quantity > remaining:
        raise InvalidOrderTransitionError(f"invalid ship quantity for line {line.id}")
    if not line.reservation_id:
        raise InvalidOrderTransitionError(f"line {line.id} без reservation_id")
    inventory_service.ship_reservation_quantity(session, line.reservation_id, quantity)
    line.quantity_shipped += quantity
    reservation = session.get(Reservation, line.reservation_id)
    if reservation is not None and reservation.quantity == 0:
        line.reservation_id = None


# Частичная отгрузка позиции (заказ остаётся в ASSEMBLING, пока не отгружено всё).
def ship_order_line(session: Session, order_id: str, line_id: str, quantity: int) -> Order:
    order = _load_order(session, order_id)
    if order.status != OrderStatus.ASSEMBLING:
        raise InvalidOrderTransitionError("partial ship only in ASSEMBLING")
    line = next((ln for ln in order.lines if ln.id == line_id), None)
    if line is None:
        raise OrderNotFoundError(order_id)
    _ship_line_quantity(session, order, line, quantity)
    if all(ln.quantity_shipped >= ln.quantity for ln in order.lines):
        assert_transition(order.status, OrderStatus.SHIPPED)
        order.status = OrderStatus.SHIPPED
    session.flush()
    return order


# Отгрузка: ASSEMBLING → SHIPPED через inventory ship.
def ship_order(session: Session, order_id: str) -> Order:
    order = _load_order(session, order_id)
    assert_transition(order.status, OrderStatus.SHIPPED)
    for line in order.lines:
        remaining = line.quantity - line.quantity_shipped
        if remaining > 0:
            _ship_line_quantity(session, order, line, remaining)
    order.status = OrderStatus.SHIPPED
    session.flush()
    return order


def complete_order(session: Session, order_id: str) -> Order:
    order = _load_order(session, order_id)
    assert_transition(order.status, OrderStatus.COMPLETED)
    order.status = OrderStatus.COMPLETED
    session.flush()
    return order


# Перевод RESERVED → PAID (только после успешной оплаты).
def mark_paid(session: Session, order_id: str) -> Order:
    order = _load_order(session, order_id)
    assert_transition(order.status, OrderStatus.PAID)
    order.status = OrderStatus.PAID
    session.flush()
    return order


def _load_order(session: Session, order_id: str) -> Order:
    stmt = select(Order).options(joinedload(Order.lines)).where(Order.id == order_id)
    order = session.scalars(stmt).unique().first()
    if order is None:
        raise OrderNotFoundError(order_id)
    return order
