class CatalogError(Exception):
    pass


class ProductNotFoundError(CatalogError):
    def __init__(self, sku: str) -> None:
        super().__init__(f"product not found: {sku}")
