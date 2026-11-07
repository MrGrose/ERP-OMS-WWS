import enum


class WarehouseTransferStatus(enum.StrEnum):
    DRAFT = "DRAFT"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
