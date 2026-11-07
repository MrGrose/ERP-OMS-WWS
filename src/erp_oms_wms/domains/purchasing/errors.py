class PurchasingError(Exception):
    pass


class PurchaseOrderNotFoundError(PurchasingError):
    pass


class GoodsReceiptNotFoundError(PurchasingError):
    pass


class InvalidPurchasingTransitionError(PurchasingError):
    pass
