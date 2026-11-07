from erp_oms_wms.domains.orders.enums import OrderStatus

# CONFIRMED: исходный ТЗ docs/requirements/ERP-OMS-WMS.md §9
ALLOWED_TRANSITIONS: dict[OrderStatus, frozenset[OrderStatus]] = {
    OrderStatus.DRAFT: frozenset({OrderStatus.CONFIRMED, OrderStatus.CANCELLED}),
    OrderStatus.CONFIRMED: frozenset({OrderStatus.RESERVED, OrderStatus.CANCELLED}),
    OrderStatus.RESERVED: frozenset(
        {OrderStatus.PAID, OrderStatus.CANCELLED, OrderStatus.ASSEMBLING},
    ),
    OrderStatus.PAID: frozenset({OrderStatus.ASSEMBLING, OrderStatus.CANCELLED}),
    OrderStatus.ASSEMBLING: frozenset({OrderStatus.SHIPPED, OrderStatus.CANCELLED}),
    OrderStatus.SHIPPED: frozenset({OrderStatus.COMPLETED}),
    OrderStatus.COMPLETED: frozenset(),
    OrderStatus.CANCELLED: frozenset(),
}


def assert_transition(current: OrderStatus, target: OrderStatus) -> None:
    allowed = ALLOWED_TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        msg = f"Переход заказа {current.value} -> {target.value} запрещен"
        from erp_oms_wms.domains.orders.errors import InvalidOrderTransitionError

        raise InvalidOrderTransitionError(msg)
