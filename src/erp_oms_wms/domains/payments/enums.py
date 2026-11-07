import enum


class PaymentAttemptStatus(enum.StrEnum):
    CREATED = "CREATED"
    PENDING = "PENDING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
