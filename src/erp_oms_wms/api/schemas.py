from pydantic import BaseModel, Field


class OrderLineIn(BaseModel):
    warehouse_id: str
    sku: str
    quantity: int = Field(gt=0)


class OrderCreateIn(BaseModel):
    customer_id: str | None = None
    lines: list[OrderLineIn]


class OrderLineOut(BaseModel):
    id: str
    warehouse_id: str
    sku: str
    quantity: int
    quantity_shipped: int
    unit_price_cents: int | None
    reservation_id: str | None

    model_config = {"from_attributes": True}


class OrderOut(BaseModel):
    id: str
    status: str
    customer_id: str | None
    lines: list[OrderLineOut]

    model_config = {"from_attributes": True}


class InventoryLevelOut(BaseModel):
    warehouse_id: str
    sku: str
    on_hand: int
    reserved: int
    available: int

    model_config = {"from_attributes": True}


class ReceiptIn(BaseModel):
    warehouse_id: str
    sku: str
    quantity: int = Field(gt=0)
    reference_id: str


class InvoiceIssueIn(BaseModel):
    order_id: str
    amount_cents: int | None = Field(default=None, gt=0)
    currency: str = "RUB"
    payment_deadline_hours: int = Field(default=24, gt=0)


class InvoiceOut(BaseModel):
    id: str
    order_id: str
    status: str
    amount_cents: int
    currency: str

    model_config = {"from_attributes": True}


class PaymentAttemptCreateIn(BaseModel):
    invoice_id: str
    provider: str = "mock"


class PaymentWebhookIn(BaseModel):
    payment_attempt_id: str
    external_event_id: str
    succeeded: bool
    failure_reason: str | None = None


class PaymentAttemptOut(BaseModel):
    id: str
    invoice_id: str
    status: str
    external_event_id: str | None

    model_config = {"from_attributes": True}


class PurchaseOrderLineIn(BaseModel):
    warehouse_id: str
    sku: str
    quantity_ordered: int = Field(gt=0)


class PurchaseOrderCreateIn(BaseModel):
    supplier_id: str
    lines: list[PurchaseOrderLineIn]


class PurchaseOrderOut(BaseModel):
    id: str
    supplier_id: str
    status: str

    model_config = {"from_attributes": True}


class GoodsReceiptLineIn(BaseModel):
    purchase_order_line_id: str
    quantity: int = Field(gt=0)


class GoodsReceiptCreateIn(BaseModel):
    purchase_order_id: str
    lines: list[GoodsReceiptLineIn]


class GoodsReceiptOut(BaseModel):
    id: str
    purchase_order_id: str
    status: str

    model_config = {"from_attributes": True}


class ProductCreateIn(BaseModel):
    sku: str
    name: str


class ProductOut(BaseModel):
    sku: str
    name: str
    is_active: bool

    model_config = {"from_attributes": True}


class SupplierCreateIn(BaseModel):
    code: str
    name: str


class SupplierOut(BaseModel):
    id: str
    code: str
    name: str
    is_active: bool

    model_config = {"from_attributes": True}


class WarehouseCreateIn(BaseModel):
    id: str
    name: str


class WarehouseOut(BaseModel):
    id: str
    name: str
    is_active: bool

    model_config = {"from_attributes": True}


class WarehouseTransferCreateIn(BaseModel):
    from_warehouse_id: str
    to_warehouse_id: str
    sku: str
    quantity: int = Field(gt=0)


class WarehouseTransferOut(BaseModel):
    id: str
    from_warehouse_id: str
    to_warehouse_id: str
    sku: str
    quantity: int
    status: str

    model_config = {"from_attributes": True}


class ReturnCreateIn(BaseModel):
    order_id: str
    warehouse_id: str
    sku: str
    quantity: int = Field(gt=0)
    reason: str | None = None


class ReturnRequestOut(BaseModel):
    id: str
    order_id: str
    warehouse_id: str
    sku: str
    quantity: int
    status: str
    reason: str | None

    model_config = {"from_attributes": True}


class AuditLogOut(BaseModel):
    id: str
    actor: str
    action: str
    entity_type: str
    entity_id: str
    details: str | None

    model_config = {"from_attributes": True}


class CustomerCreateIn(BaseModel):
    name: str
    email: str | None = None
    price_list: str = "RETAIL"


class CustomerOut(BaseModel):
    id: str
    name: str
    email: str | None
    price_list: str
    is_active: bool

    model_config = {"from_attributes": True}


class ProductPriceUpsertIn(BaseModel):
    price_list: str
    sku: str
    amount_cents: int = Field(ge=0)
    currency: str = "RUB"


class ProductPriceOut(BaseModel):
    price_list: str
    sku: str
    amount_cents: int
    currency: str

    model_config = {"from_attributes": True}


class SupplierProductCreateIn(BaseModel):
    sku: str
    supplier_sku: str
    purchase_price_cents: int = Field(ge=0)
    lead_time_days: int = Field(ge=0, default=0)


class SupplierProductOut(BaseModel):
    id: str
    supplier_id: str
    sku: str
    supplier_sku: str
    purchase_price_cents: int
    lead_time_days: int
    is_active: bool

    model_config = {"from_attributes": True}


class StockMovementOut(BaseModel):
    id: str
    movement_type: str
    warehouse_id: str
    sku: str
    on_hand_delta: int
    reserved_delta: int
    reference_type: str | None
    reference_id: str | None
    reason: str | None

    model_config = {"from_attributes": True}


class ReservationOut(BaseModel):
    id: str
    order_id: str
    warehouse_id: str
    sku: str
    quantity: int
    status: str

    model_config = {"from_attributes": True}


class OrderLineShipIn(BaseModel):
    quantity: int = Field(gt=0)


class StockReportRow(BaseModel):
    warehouse_id: str
    sku: str
    on_hand: int
    reserved: int
    available: int
