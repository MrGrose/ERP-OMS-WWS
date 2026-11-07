class SupplierError(Exception):
    pass


class SupplierNotFoundError(SupplierError):
    def __init__(self, supplier_id: str) -> None:
        super().__init__(f"supplier not found: {supplier_id}")


class SupplierProductNotFoundError(SupplierError):
    def __init__(self, product_id: str) -> None:
        super().__init__(f"supplier product not found: {product_id}")
