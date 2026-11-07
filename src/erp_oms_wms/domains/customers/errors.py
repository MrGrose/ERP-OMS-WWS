class CustomerError(Exception):
    pass


class CustomerNotFoundError(CustomerError):
    def __init__(self, customer_id: str) -> None:
        super().__init__(f"customer not found: {customer_id}")


class CustomerInactiveError(CustomerError):
    def __init__(self, customer_id: str) -> None:
        super().__init__(f"customer inactive: {customer_id}")
