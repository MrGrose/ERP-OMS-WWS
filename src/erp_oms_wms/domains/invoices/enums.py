import enum


class InvoiceStatus(enum.StrEnum):
    ISSUED = "ISSUED"
    PENDING_PAYMENT = "PENDING_PAYMENT"
    PAID = "PAID"
    EXPIRED = "EXPIRED"
