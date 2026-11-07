# Mini ERP / OMS / WMS Backend

## 1. Идея проекта

**Mini ERP / OMS / WMS** — универсальный backend для управления товарами, закупками, остатками, заказами, резервами, поставщиками, счетами и движением товара.

Цель проекта — показать сильную предметную модель и backend engineering вокруг реальной коммерческой логики.

Это не попытка сделать полноценную 1С.

Это компактная backend-система, которая демонстрирует понимание:

- inventory;
- order management;
- warehouse operations;
- purchasing;
- reservations;
- financial state;
- pricing;
- audit;
- concurrency;
- transactional consistency.

---

# 2. Что проект должен проверять

Проект должен демонстрировать:

- сложное domain modeling;
- PostgreSQL;
- transactions;
- inventory consistency;
- stock reservations;
- concurrency;
- state machines;
- order lifecycle;
- purchase lifecycle;
- invoice lifecycle;
- audit trail;
- background jobs;
- reporting;
- permissions;
- idempotency;
- integration design.

Главный вопрос проекта:

> Как гарантировать, что бизнес-состояние и остатки остаются корректными при конкурентных операциях и сбоях?

---

# 3. Основные домены

```text
Catalog
Customers
Suppliers
Warehouses
Inventory
Purchasing
Orders
Invoices
Payments
Returns
Pricing
Audit
```

---

# 4. Product Catalog

Модель товара:

```text
Product
SKU
Barcode
Category
Brand
Unit
Price
Cost
Status
```

Поддержать:

- SKU;
- barcode;
- supplier SKU;
- units;
- active/inactive;
- price lists;
- cost price.

Не делать каталог просто CRUD-таблицей.

У товара должны быть бизнес-ограничения.

---

# 5. Warehouses

Поддержать несколько складов:

```text
Warehouse A
Warehouse B
Warehouse C
```

Остатки:

```text
Product
+
Warehouse
=
Stock
```

Например:

```text
SKU-001
Warehouse-1
on_hand = 100
reserved = 20
available = 80
```

Важно явно определить:

```text
available = on_hand - reserved
```

и поддерживать этот инвариант.

---

# 6. Stock Movements

Нельзя просто изменять:

```text
stock.quantity -= 10
```

без истории.

Создать журнал движений:

```text
StockMovement
```

Типы:

```text
RECEIPT
RESERVATION
RELEASE
SHIPMENT
RETURN
ADJUSTMENT
TRANSFER
```

Каждое изменение остатка должно иметь причину.

Пример:

```text
100
 ↓ shipment -10
90
 ↓ receipt +50
140
```

История должна быть аудируемой.

---

# 7. Reservations

Резервирование товара:

```text
Order
 ↓
Reservation
 ↓
Stock.reserved += quantity
```

Например:

```text
on_hand = 10
reserved = 3
available = 7
```

Нельзя зарезервировать больше доступного:

```text
available < requested
→ reject
```

---

# 8. Concurrency

Один из главных тестов проекта:

```text
Stock available = 1

Request A → reserve 1
Request B → reserve 1
```

Один должен победить.

Второй должен получить:

```text
insufficient stock
```

Не допускается:

```text
reserved = 2
available = -1
```

Реализовать и протестировать:

- `SELECT FOR UPDATE`;
- optimistic locking;
- atomic update;

выбрав подходящий вариант.

---

# 9. Orders

Order lifecycle:

```text
DRAFT
 ↓
CONFIRMED
 ↓
RESERVED
 ↓
PAID
 ↓
ASSEMBLING
 ↓
SHIPPED
 ↓
COMPLETED
```

Также:

```text
CANCELLED
```

Переходы должны быть ограничены.

Например:

```text
COMPLETED → DRAFT
```

недопустим.

State machine должна быть явно выражена в коде.

---

# 10. Invoice lifecycle

Например:

```text
ISSUED
 ↓
PENDING_PAYMENT
 ↓
PAID
```

или:

```text
PENDING_PAYMENT
 ↓
EXPIRED
```

При expiration:

```text
Invoice expired
 ↓
Reservation released
```

Это важная транзакционная связь.

---

# 11. Payments

Не хранить просто:

```text
order.is_paid = true
```

Создать payment attempts:

```text
PaymentAttempt
```

Состояния:

```text
CREATED
PENDING
SUCCEEDED
FAILED
CANCELLED
```

Поддержать:

- external payment ID;
- amount;
- currency;
- provider;
- timestamps;
- failure reason.

Это позволяет показать reconciliation/idempotency.

---

# 12. Purchasing

Supplier flow:

```text
Purchase Order
 ↓
Supplier
 ↓
Items
 ↓
Receipt
 ↓
Stock increase
```

Например:

```text
PurchaseOrder
PurchaseOrderItem
GoodsReceipt
GoodsReceiptItem
```

После приёмки:

```text
StockMovement(RECEIPT)
```

---

# 13. Supplier management

Supplier:

```text
Supplier
SupplierProduct
SupplierPrice
```

Поддержать:

- supplier SKU;
- purchase price;
- lead time;
- active status.

Опционально:

- minimum order quantity;
- supplier priority.

---

# 14. Pricing

Сделать несколько price lists:

```text
RETAIL
WHOLESALE
B2B
SPECIAL
```

Цена должна определяться по правилам.

Например:

```text
Customer
 ↓
PriceList
 ↓
Product
 ↓
Price
```

Не зашивать цену непосредственно в order logic.

---

# 15. Returns

Return flow:

```text
Order
 ↓
Return request
 ↓
Approved
 ↓
Received
 ↓
Stock movement
```

Возврат должен корректно влиять на inventory.

---

# 16. Warehouse transfer

Поддержать перемещение:

```text
Warehouse A
     ↓
Transfer
     ↓
Warehouse B
```

Например:

```text
A stock -10
B stock +10
```

Операция должна быть транзакционной.

---

# 17. Audit log

Каждое важное business action должно оставлять audit record:

```text
actor
action
entity
entity_id
timestamp
before
after
metadata
```

Например:

```text
user 42
RESERVE_STOCK
SKU-001
quantity 5
```

Audit log нельзя редактировать обычным пользователем.

---

# 18. Idempotency

Особенно важно для:

- payment callbacks;
- goods receipts;
- stock adjustments;
- order confirmation;
- external integrations.

Например:

```text
payment webhook
external_event_id = abc123
```

Если webhook приходит дважды:

```text
first → process
second → ignore
```

---

# 19. Background jobs

Использовать ARQ/RQ/Celery или другой обоснованный механизм.

Примеры:

```text
expire_invoices
release_expired_reservations
sync_supplier_prices
generate_reports
reconcile_payments
send_notifications
```

Каждая job должна быть:

- retryable;
- observable;
- idempotent где необходимо.

---

# 20. Reporting

Добавить backend endpoints для:

- current stock;
- reserved stock;
- inventory movements;
- sales;
- purchases;
- unpaid invoices;
- supplier balances;
- stock turnover.

Не нужно делать полноценный BI.

Главное — показать сложные SQL queries и aggregation.

---

# 21. PostgreSQL

Использовать:

- constraints;
- foreign keys;
- indexes;
- unique constraints;
- transactions;
- locking;
- aggregation;
- window functions там, где это оправдано.

Особенно продемонстрировать:

```text
SKU + warehouse
```

как уникальную пару.

---

# 22. Authentication / Authorization

Минимально:

```text
Admin
Manager
WarehouseOperator
Accountant
```

Permissions:

```text
catalog.read
catalog.write
inventory.read
inventory.adjust
orders.read
orders.manage
payments.read
finance.read
```

Не ограничиваться только `is_admin`.

---

# 23. API

Основные endpoints:

```text
/products
/warehouses
/inventory
/inventory/movements
/reservations
/orders
/invoices
/payments
/purchases
/suppliers
/returns
/transfers
/audit
/reports
```

Swagger/OpenAPI.

---

# 24. Testing

### Unit

- state transitions;
- pricing;
- reservation rules;
- invoice expiration.

### Integration

- PostgreSQL;
- stock movements;
- order lifecycle;
- payment callbacks.

### Concurrency

Обязательно:

- concurrent reservation;
- concurrent payment callback;
- warehouse transfer race.

### Invariants

Проверять:

```text
available >= 0
reserved >= 0
```

и другие бизнес-инварианты.

---

# 25. Docker

Минимально:

```text
api
postgres
redis
worker
```

Опционально:

```text
minio
```

---

# 26. CI/CD

GitHub Actions:

```text
lint
 ↓
unit tests
 ↓
integration tests
 ↓
Docker build
```

---

# 27. Что особенно важно

Не превращать проект в:

```text
Product CRUD
Order CRUD
Warehouse CRUD
```

Ценность находится в связях:

```text
Order
 ↓
Reservation
 ↓
Inventory
 ↓
Payment
 ↓
Invoice
 ↓
Shipment
 ↓
Stock movement
```

и:

```text
Purchase
 ↓
Goods receipt
 ↓
Stock movement
 ↓
Inventory
```

---

# 28. Главные технические задачи

Проект должен иметь несколько задач, которые действительно требуют инженерного решения:

### Task 1 — Reservation consistency

Как безопасно резервировать последний товар при двух одновременных запросах?

### Task 2 — Invoice expiration

Как автоматически освободить reservation при истечении invoice?

### Task 3 — Payment idempotency

Как обработать один payment webhook несколько раз?

### Task 4 — Stock auditability

Как узнать, почему остаток изменился?

### Task 5 — Warehouse transfer

Как атомарно переместить товар между складами?

### Task 6 — Order state machine

Как запретить невозможные переходы?

### Task 7 — Authorization

Как отделить права склада, продаж и финансов?

---

# 29. Что проект показывает работодателю

После просмотра должно быть видно:

> Разработчик понимает предметную область commerce/ERP/WMS и умеет переводить бизнес-процессы в согласованную backend-модель.

Это уже не просто знание FastAPI.

---

# 30. Итоговый CV-сигнал

После фактической реализации можно честно написать:

- Designed modular ERP/OMS/WMS backend for inventory, orders, purchasing and invoicing.
- Implemented concurrency-safe inventory reservations and stock movement ledger.
- Built order and invoice state machines with transactional reservation release.
- Implemented idempotent payment callbacks and reconciliation jobs.
- Added warehouse transfers, supplier purchasing and audit trail.
- Designed PostgreSQL schema with transactional constraints, indexes and locking.
- Added role-based permissions and integration/concurrency tests.

Использовать только те формулировки, которые подтверждаются реальным кодом.
