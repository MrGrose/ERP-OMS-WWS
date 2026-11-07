from erp_oms_wms.domains.purchasing.enums import GoodsReceiptStatus, PurchaseOrderStatus

PO_TRANSITIONS: dict[PurchaseOrderStatus, frozenset[PurchaseOrderStatus]] = {
    PurchaseOrderStatus.DRAFT: frozenset(
        {PurchaseOrderStatus.CONFIRMED, PurchaseOrderStatus.CANCELLED}
    ),
    PurchaseOrderStatus.CONFIRMED: frozenset(
        {PurchaseOrderStatus.RECEIVED, PurchaseOrderStatus.CANCELLED}
    ),
    PurchaseOrderStatus.RECEIVED: frozenset(),
    PurchaseOrderStatus.CANCELLED: frozenset(),
}

GR_TRANSITIONS: dict[GoodsReceiptStatus, frozenset[GoodsReceiptStatus]] = {
    GoodsReceiptStatus.DRAFT: frozenset(
        {GoodsReceiptStatus.CONFIRMED, GoodsReceiptStatus.CANCELLED}
    ),
    GoodsReceiptStatus.CONFIRMED: frozenset(),
    GoodsReceiptStatus.CANCELLED: frozenset(),
}


def assert_po_transition(current: PurchaseOrderStatus, target: PurchaseOrderStatus) -> None:
    if target not in PO_TRANSITIONS.get(current, frozenset()):
        from erp_oms_wms.domains.purchasing.errors import InvalidPurchasingTransitionError

        raise InvalidPurchasingTransitionError(f"PO {current.value} → {target.value} запрещён")


def assert_gr_transition(current: GoodsReceiptStatus, target: GoodsReceiptStatus) -> None:
    if target not in GR_TRANSITIONS.get(current, frozenset()):
        from erp_oms_wms.domains.purchasing.errors import InvalidPurchasingTransitionError

        raise InvalidPurchasingTransitionError(f"GR {current.value} → {target.value} запрещён")
