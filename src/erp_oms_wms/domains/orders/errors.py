class OrderError(Exception):
    pass


class InvalidOrderTransitionError(OrderError):
    pass


class OrderNotFoundError(OrderError):
    pass
