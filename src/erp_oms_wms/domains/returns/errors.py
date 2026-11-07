class ReturnError(Exception):
    pass


class ReturnNotFoundError(ReturnError):
    def __init__(self, return_id: str) -> None:
        super().__init__(f"return not found: {return_id}")


class InvalidReturnTransitionError(ReturnError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class ReturnOrderNotEligibleError(ReturnError):
    def __init__(self, order_id: str, status: str) -> None:
        super().__init__(f"order {order_id} not eligible for return (status {status})")
