from sqlalchemy import select
from sqlalchemy.orm import Session

from erp_oms_wms.domains.inventory.enums import ReservationStatus, StockMovementType
from erp_oms_wms.domains.inventory.errors import (
    InsufficientAvailableError,
    InvalidReservationTransitionError,
    InventoryLevelNotFoundError,
    ReservationNotFoundError,
)
from erp_oms_wms.domains.inventory.models import InventoryLevel, Reservation, StockMovement


# Возвращает строку остатка с блокировкой FOR UPDATE или None.
def _get_level_for_update(
    session: Session,
    warehouse_id: str,
    sku: str,
) -> InventoryLevel | None:
    stmt = (
        select(InventoryLevel)
        .where(
            InventoryLevel.warehouse_id == warehouse_id,
            InventoryLevel.sku == sku,
        )
        .with_for_update()
    )
    return session.scalars(stmt).first()


# Пишет запись в журнал движений и применяет дельты к уровню остатка.
def _append_movement(
    session: Session,
    level: InventoryLevel,
    movement_type: StockMovementType,
    on_hand_delta: int,
    reserved_delta: int,
    reference_type: str | None,
    reference_id: str | None,
    reason: str | None = None,
) -> StockMovement:
    level.on_hand += on_hand_delta
    level.reserved += reserved_delta
    movement = StockMovement(
        movement_type=movement_type,
        warehouse_id=level.warehouse_id,
        sku=level.sku,
        on_hand_delta=on_hand_delta,
        reserved_delta=reserved_delta,
        reference_type=reference_type,
        reference_id=reference_id,
        reason=reason,
    )
    session.add(movement)
    return movement


# Проверяет, хватает ли available под резерв (без записи).
def check_available(session: Session, warehouse_id: str, sku: str, quantity: int) -> None:
    level = _get_level_for_update(session, warehouse_id, sku)
    if level is None:
        raise InsufficientAvailableError(sku, warehouse_id, quantity, 0)
    if quantity > level.available:
        raise InsufficientAvailableError(sku, warehouse_id, quantity, level.available)


# Создаёт или возвращает уровень остатка для пары склад+SKU.
def ensure_inventory_level(
    session: Session,
    warehouse_id: str,
    sku: str,
    *,
    initial_on_hand: int = 0,
) -> InventoryLevel:
    level = session.scalars(
        select(InventoryLevel).where(
            InventoryLevel.warehouse_id == warehouse_id,
            InventoryLevel.sku == sku,
        ),
    ).first()
    if level is not None:
        return level
    level = InventoryLevel(
        warehouse_id=warehouse_id,
        sku=sku,
        on_hand=initial_on_hand,
        reserved=0,
    )
    session.add(level)
    session.flush()
    return level


# Увеличивает on_hand с записью RECEIPT (основание — внешняя ссылка).
def apply_receipt(
    session: Session,
    warehouse_id: str,
    sku: str,
    quantity: int,
    reference_type: str,
    reference_id: str,
) -> InventoryLevel:
    if quantity <= 0:
        raise ValueError("quantity must be positive")
    ensure_inventory_level(session, warehouse_id, sku)
    locked = _get_level_for_update(session, warehouse_id, sku)
    if locked is None:
        raise InventoryLevelNotFoundError(f"Нет остатка {sku} на складе {warehouse_id}")
    _append_movement(
        session,
        locked,
        StockMovementType.RECEIPT,
        on_hand_delta=quantity,
        reserved_delta=0,
        reference_type=reference_type,
        reference_id=reference_id,
        reason="receipt",
    )
    session.flush()
    return locked


# Резервирует доступное количество под заказ (BR-003, BR-010).
def reserve_for_order(
    session: Session,
    *,
    order_id: str,
    warehouse_id: str,
    sku: str,
    quantity: int,
) -> Reservation:
    if quantity <= 0:
        raise ValueError("quantity must be positive")
    level = _get_level_for_update(session, warehouse_id, sku)
    if level is None:
        raise InventoryLevelNotFoundError(f"Нет остатка {sku} на складе {warehouse_id}")
    available = level.available
    if quantity > available:
        raise InsufficientAvailableError(sku, warehouse_id, quantity, available)
    reservation = Reservation(
        order_id=order_id,
        warehouse_id=warehouse_id,
        sku=sku,
        quantity=quantity,
        status=ReservationStatus.ACTIVE,
    )
    session.add(reservation)
    session.flush()
    _append_movement(
        session,
        level,
        StockMovementType.RESERVATION,
        on_hand_delta=0,
        reserved_delta=quantity,
        reference_type="reservation",
        reference_id=reservation.id,
        reason=f"order {order_id}",
    )
    session.flush()
    return reservation


# Освобождает активный резерв (RELEASE).
def release_reservation(session: Session, reservation_id: str) -> Reservation:
    reservation = session.get(Reservation, reservation_id)
    if reservation is None:
        raise ReservationNotFoundError(reservation_id)
    if reservation.status != ReservationStatus.ACTIVE:
        raise InvalidReservationTransitionError(
            f"reservation {reservation_id} status {reservation.status.value}",
        )
    level = _get_level_for_update(session, reservation.warehouse_id, reservation.sku)
    if level is None:
        raise InventoryLevelNotFoundError(reservation.sku)
    qty = reservation.quantity
    _append_movement(
        session,
        level,
        StockMovementType.RELEASE,
        on_hand_delta=0,
        reserved_delta=-qty,
        reference_type="reservation",
        reference_id=reservation.id,
        reason="release",
    )
    reservation.status = ReservationStatus.RELEASED
    session.flush()
    return reservation


def ship_reservation_quantity(session: Session, reservation_id: str, quantity: int) -> Reservation:
    if quantity <= 0:
        raise ValueError("quantity must be positive")
    reservation = session.get(Reservation, reservation_id)
    if reservation is None:
        raise ReservationNotFoundError(reservation_id)
    if reservation.status not in (ReservationStatus.ACTIVE, ReservationStatus.PARTIALLY_SHIPPED):
        raise InvalidReservationTransitionError(
            f"reservation {reservation_id} status {reservation.status.value}",
        )
    if quantity > reservation.quantity:
        raise ValueError("quantity exceeds reservation")
    level = _get_level_for_update(session, reservation.warehouse_id, reservation.sku)
    if level is None:
        raise InventoryLevelNotFoundError(reservation.sku)
    _append_movement(
        session,
        level,
        StockMovementType.SHIPMENT,
        on_hand_delta=-quantity,
        reserved_delta=-quantity,
        reference_type="reservation",
        reference_id=reservation.id,
        reason="partial shipment" if quantity < reservation.quantity else "shipment",
    )
    reservation.quantity -= quantity
    if reservation.quantity == 0:
        reservation.status = ReservationStatus.SHIPPED
    else:
        reservation.status = ReservationStatus.PARTIALLY_SHIPPED
    session.flush()
    return reservation


# Отгрузка: уменьшает on_hand и reserved (SHIPMENT).
def ship_reservation(session: Session, reservation_id: str) -> Reservation:
    reservation = session.get(Reservation, reservation_id)
    if reservation is None:
        raise ReservationNotFoundError(reservation_id)
    if reservation.status not in (ReservationStatus.ACTIVE, ReservationStatus.PARTIALLY_SHIPPED):
        raise InvalidReservationTransitionError(
            f"reservation {reservation_id} status {reservation.status.value}",
        )
    qty = reservation.quantity
    return ship_reservation_quantity(session, reservation_id, qty)


def _lock_warehouse_skus(session: Session, warehouse_ids: list[str], sku: str) -> None:
    for wh in sorted(set(warehouse_ids)):
        _get_level_for_update(session, wh, sku)


# Атомарное перемещение available между складами (два движения TRANSFER).
def transfer_stock(
    session: Session,
    *,
    from_warehouse_id: str,
    to_warehouse_id: str,
    sku: str,
    quantity: int,
    reference_type: str,
    reference_id: str,
) -> tuple[InventoryLevel, InventoryLevel]:
    if quantity <= 0:
        raise ValueError("quantity must be positive")
    if from_warehouse_id == to_warehouse_id:
        raise ValueError("source and destination warehouse must differ")
    ensure_inventory_level(session, from_warehouse_id, sku)
    ensure_inventory_level(session, to_warehouse_id, sku)
    _lock_warehouse_skus(session, [from_warehouse_id, to_warehouse_id], sku)
    src = _get_level_for_update(session, from_warehouse_id, sku)
    dst = _get_level_for_update(session, to_warehouse_id, sku)
    assert src is not None and dst is not None
    if quantity > src.available:
        raise InsufficientAvailableError(sku, from_warehouse_id, quantity, src.available)
    _append_movement(
        session,
        src,
        StockMovementType.TRANSFER,
        on_hand_delta=-quantity,
        reserved_delta=0,
        reference_type=reference_type,
        reference_id=reference_id,
        reason=f"transfer to {to_warehouse_id}",
    )
    _append_movement(
        session,
        dst,
        StockMovementType.TRANSFER,
        on_hand_delta=quantity,
        reserved_delta=0,
        reference_type=reference_type,
        reference_id=reference_id,
        reason=f"transfer from {from_warehouse_id}",
    )
    session.flush()
    return src, dst


# Возврат на склад (RETURN, +on_hand).
def apply_return(
    session: Session,
    *,
    warehouse_id: str,
    sku: str,
    quantity: int,
    reference_type: str,
    reference_id: str,
    reason: str | None = None,
) -> InventoryLevel:
    if quantity <= 0:
        raise ValueError("quantity must be positive")
    ensure_inventory_level(session, warehouse_id, sku)
    locked = _get_level_for_update(session, warehouse_id, sku)
    if locked is None:
        raise InventoryLevelNotFoundError(f"Нет остатка {sku} на складе {warehouse_id}")
    _append_movement(
        session,
        locked,
        StockMovementType.RETURN,
        on_hand_delta=quantity,
        reserved_delta=0,
        reference_type=reference_type,
        reference_id=reference_id,
        reason=reason or "return",
    )
    session.flush()
    return locked
