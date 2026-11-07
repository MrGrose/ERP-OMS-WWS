import enum


class StockMovementType(enum.StrEnum):
    RECEIPT = "RECEIPT"
    RESERVATION = "RESERVATION"
    RELEASE = "RELEASE"
    SHIPMENT = "SHIPMENT"
    RETURN = "RETURN"
    ADJUSTMENT = "ADJUSTMENT"
    TRANSFER = "TRANSFER"


class ReservationStatus(enum.StrEnum):
    ACTIVE = "ACTIVE"
    SHIPPED = "SHIPPED"
    RELEASED = "RELEASED"
    PARTIALLY_SHIPPED = "PARTIALLY_SHIPPED"
