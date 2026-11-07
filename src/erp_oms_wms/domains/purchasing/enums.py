import enum


class PurchaseOrderStatus(enum.StrEnum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    RECEIVED = "RECEIVED"
    CANCELLED = "CANCELLED"


class GoodsReceiptStatus(enum.StrEnum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
