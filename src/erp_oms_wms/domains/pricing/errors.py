class PricingError(Exception):
    pass


class PriceNotFoundError(PricingError):
    def __init__(self, price_list: str, sku: str) -> None:
        super().__init__(f"no price for {sku} in {price_list}")
