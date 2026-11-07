class PaymentError(Exception):
    pass


class PaymentAttemptNotFoundError(PaymentError):
    pass


class InvalidPaymentTransitionError(PaymentError):
    pass


class IdempotentReplayError(PaymentError):
    def __init__(self, attempt_id: str, status: str) -> None:
        self.attempt_id = attempt_id
        self.status = status
        super().__init__(attempt_id)
