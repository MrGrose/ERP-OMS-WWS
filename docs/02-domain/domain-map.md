# Карта доменов (as-built)

**Статус:** Backend MVP. Пакеты: `src/erp_oms_wms/domains/<name>/`.

## Матрица

| Домен | Модели (основные) | API router | Статус |
|-------|-------------------|------------|--------|
| catalog | `Product` | `catalog` | **IMPLEMENTED** |
| warehouses | `Warehouse` | `warehouses` | **IMPLEMENTED** |
| inventory | `InventoryLevel`, `StockMovement`, `Reservation` | `inventory` | **IMPLEMENTED** |
| pricing | `ProductPrice` | `pricing` | **IMPLEMENTED** |
| customers | `Customer` | `customers` | **IMPLEMENTED** |
| orders | `Order`, `OrderLine` | `orders` | **IMPLEMENTED** |
| invoices | `Invoice` | `invoices` | **IMPLEMENTED** |
| payments | `PaymentAttempt` | `payments` | **IMPLEMENTED** |
| suppliers | `Supplier`, `SupplierProduct` | `suppliers` | **IMPLEMENTED** |
| purchasing | `PurchaseOrder`, `GoodsReceipt`, lines | `purchasing` | **IMPLEMENTED** |
| transfers | `WarehouseTransfer` | `transfers` | **IMPLEMENTED** |
| returns | `ReturnRequest` | `returns` | **PARTIAL** (без refund) |
| audit | `AuditLog` | `audit` | **IMPLEMENTED** |
| reporting | (без отдельных ORM в отчётах) | `reports` | **IMPLEMENTED** |

Отдельного markdown `catalog.md` нет; каталог описан здесь и в ТЗ.

## Ключевые зависимости

```text
Orders ──reserve/ship──► Inventory
Orders ──invoice──────► Invoices ──payment──► Payments
Purchasing ──receipt──► Inventory (RECEIPT)
Transfers / Returns ───► Inventory (TRANSFER / RETURN)
Orders.confirm ─────────► Pricing (фиксация unit_price_cents)
```

## Инварианты границ

- Только **Inventory** изменяет `on_hand` и `reserved` на `InventoryLevel`.
- **Payments** — источник истины оплаты (`PaymentAttempt`).
- Orders **не** пишет в таблицы остатков напрямую.

## OUT OF SCOPE в коде

- GL, double-entry, 1С.
- `Shipment` как сущность, warehouse zones/bins, customer addresses.
- JWT, реальный PSP.

## Документы по доменам

| Файл | Тема |
|------|------|
| [`../05-data-integrity/concurrency.md`](../05-data-integrity/concurrency.md) | Гонки за резерв |
| [`../01-overview/architecture.md`](../01-overview/architecture.md) | Слои и границы |
| [`../README.md`](../README.md) | Индекс публичной документации |
