class InventoryError(Exception):
    pass


class InsufficientAvailableError(InventoryError):
    def __init__(self, sku: str, warehouse_id: str, requested: int, available: int) -> None:
        self.sku = sku
        self.warehouse_id = warehouse_id
        self.requested = requested
        self.available = available
        super().__init__(
            f"Недостаточно товара {sku} на складе {warehouse_id}: "
            f"запрошено {requested}, доступно {available}",
        )


class InventoryLevelNotFoundError(InventoryError):
    pass


class ReservationNotFoundError(InventoryError):
    pass


class InvalidReservationTransitionError(InventoryError):
    pass
