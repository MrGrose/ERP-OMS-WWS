class WarehouseError(Exception):
    pass


class WarehouseNotFoundError(WarehouseError):
    def __init__(self, warehouse_id: str) -> None:
        super().__init__(f"warehouse not found: {warehouse_id}")
