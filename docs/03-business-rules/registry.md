# Реестр бизнес-правил (Business Rules Registry)

## Назначение
Централизованный каталог всех бизнес-правил (BR-xxx). Каждое правило связано с доменом, содержит критерии тестирования и статус.

---

## Inventory domain (BR-001 до BR-009)

### BR-001: On-hand >= 0 (CONFIRMED)
- **Домен**: Inventory
- **Описание**: Остаток товара на складе не может быть отрицательным
- **Правило**: `on_hand >= 0` всегда
- **Критерии тестирования**: 
  - ✓ on_hand = 0 разрешен (товар закончился)
  - ✗ on_hand < 0 → error, операция отклонена
- **Реализация**: Constraint в БД + validation в Inventory service
- **Ссылки**: Inventory domain, stock-movement-semantics.md

### BR-002: Reserved <= On-hand (CONFIRMED)
- **Домен**: Inventory
- **Описание**: Зарезервированное количество не может быть больше доступного
- **Правило**: `reserved <= on_hand` всегда
- **Критерии тестирования**:
  - ✓ reserved = on_hand (все зарезервировано)
  - ✗ reserved > on_hand → error
- **Реализация**: Check в Inventory service перед RESERVE операцией
- **Ссылки**: inventory.md, inventory-reservations.md

### BR-003: Available = On-hand - Reserved (CONFIRMED)
- **Домен**: Inventory
- **Описание**: Доступное количество вычисляется, не хранится
- **Правило**: `available = on_hand - reserved` (computed field)
- **Критерии тестирования**:
  - ✓ Query available не совпадает с вычисленным → bug
  - ✓ Изменить on_hand или reserved → available пересчитано
- **Реализация**: Computed field в SQL или application logic
- **Ссылки**: inventory.md

### BR-004: All balance changes = StockMovement entry + grund (CONFIRMED)
- **Домен**: Inventory
- **Описание**: Любое изменение on_hand или reserved — запись в stock_movement журнал с обоснованием
- **Правило**: `DELETE FROM stock_movement WHERE ... ` запрещен; только INSERT/SELECT
- **Критерии тестирования**:
  - ✓ +1000 on_hand → 1 запись в stock_movement с type и reference_id
  - ✗ UPDATE inventory_level SET on_hand = ... БЕЗ stock_movement → audit alert
  - ✓ Восстановить on_hand из stock_movement (SUM за период)
- **Реализация**: Trigger или service call перед UPDATE
- **Ссылки**: stock-movement-semantics.md, cross-domain-flows.md

### BR-005: Reservation doesn't decrease on_hand (CONFIRMED)
- **Домен**: Inventory
- **Описание**: Резервирование не уменьшает on_hand; это маркер на доступность
- **Правило**: RESERVE операция: reserved += qty, on_hand не изменяется
- **Критерии тестирования**:
  - ✓ on_hand=100, RESERVE(20) → on_hand=100, reserved=20, available=80
  - ✗ RESERVE(20) → on_hand=80 → error (wrong logic)
- **Реализация**: Orders инициирует RESERVE в Inventory, Inventory +reserved only
- **Ссылки**: inventory-reservations.md, orders.md

### BR-006: Reservation can be released if order cancelled/returned (CONFIRMED)
- **Домен**: Inventory
- **Описание**: Резерв может быть отменен, если заказ отменен или возвращен
- **Правило**: RELEASE операция: reserved -= qty (заказ отменен или товар возвращен)
- **Критерии тестирования**:
  - ✓ Order cancelled → RELEASE резерва → reserved -= qty
  - ✓ Товар возвращен → RELEASE + RETURN (inventory +on_hand)
  - ✗ Попытка RELEASE после SHIPMENT → error (не может быть дважды)
- **Реализация**: Orders инициирует RELEASE, Inventory обрабатывает
- **Ссылки**: inventory-reservations.md

### BR-007: Shipment includes RELEASE of reservation (CONFIRMED)
- **Домен**: Inventory
- **Описание**: Отгрузка включает снятие резерва и уменьшение on_hand
- **Правило**: SHIPMENT: on_hand -= qty, reserved -= qty (одновременно)
- **Критерии тестирования**:
  - ✓ Order RESERVED(20), then SHIPMENT(20) → on_hand -20, reserved -20
  - ✓ Partial shipment: RESERVED(20), SHIPMENT(15) → reserved=5, on_hand -15
  - ✗ SHIPMENT > RESERVED → error (можно отправить только зарезервированное)
- **Реализация**: StockMovement type=SHIPMENT обновляет оба поля
- **Ссылки**: stock-movement-semantics.md

### BR-008: Cannot reserve more than available (CONFIRMED)
- **Домен**: Inventory
- **Описание**: Новое резервирование возможно только если доступно достаточно товара
- **Правило**: `new_reservation.qty <= available` проверяется перед созданием
- **Критерии тестирования**:
  - ✓ on_hand=100, reserved=20, available=80, RESERVE(50) → ok
  - ✗ on_hand=100, reserved=20, available=80, RESERVE(100) → error
- **Реализация**: Validation в Orders / Inventory перед RESERVE
- **Ссылки**: inventory-reservations.md

### BR-009: StockMovement is append-only (CONFIRMED)
- **Домен**: Inventory
- **Описание**: Записи в stock_movement не может быть отредактирована или удалена, только добавлены компенсирующие записи
- **Правило**: DELETE/UPDATE stock_movement запрещен; только INSERT
- **Критерии тестирования**:
  - ✓ Ошибочная RECEIPT(+1000) → new ADJUSTMENT(−1000) для компенсации
  - ✗ UPDATE stock_movement SET qty_delta = ... → error
  - ✓ Восстановить состояние on_hand: SUM(qty_delta) с начала периода
- **Реализация**: DB constraint + audit на DELETE/UPDATE попытки
- **Ссылки**: stock-movement-semantics.md

---

## Orders domain (BR-010 до BR-019)

### BR-010: OrderLine.qty <= available at order creation (CONFIRMED)
- **Домен**: Orders
- **Описание**: При создании заказа проверяется доступность товара
- **Правило**: Для каждого OrderLine: `qty <= Inventory.available` в момент создания
- **Критерии тестирования**:
  - ✓ available=100, OrderLine(qty=50) → ok, RESERVE(50)
  - ✗ available=30, OrderLine(qty=50) → error, order rejected
- **Реализация**: Orders query Inventory.available перед созданием
- **Ссылки**: orders.md

### BR-011: Order can be cancelled only in DRAFT/PENDING (CONFIRMED)
- **Домен**: Orders
- **Описание**: Заказ может быть отменен только если не начата отгрузка
- **Правило**: `order.cancel()` разрешена только если status в [DRAFT, PENDING]
- **Критерии тестирования**:
  - ✓ Order DRAFT → cancel → CANCELLED, резервы освобождены
  - ✗ Order SHIPPED → cancel → error
- **Реализация**: State machine в Orders service
- **Ссылки**: cross-domain-flows.md#Flow-1

### BR-012: Shipment only after order confirmation and payment (PROPOSED)
- **Домен**: Orders
- **Описание**: Товар может быть отправлен только если заказ подтвержден и оплачен
- **Правило**: `order.ship()` возможна только если status=CONFIRMED И payment.status=SUCCESS
- **Критерии тестирования**:
  - ✓ Order CONFIRMED, Payment SUCCESS → shipment possible
  - ✗ Order CONFIRMED, Payment PENDING → shipment rejected
- **Реализация**: Check в Orders service перед SHIPMENT
- **Ссылки**: orders.md, payments.md

### BR-013: Return only within return window (PROPOSED)
- **Домен**: Orders
- **Описание**: Товар может быть возвращен только в течение установленного периода
- **Правило**: `return.create()` разрешена только если `now <= shipment.timestamp + return_window`
- **Критерии тестирования**:
  - ✓ Товар отправлен 2 дня назад, return_window=14 дней → return ok
  - ✗ Товар отправлен 20 дней назад → return rejected
- **Реализация**: Check в Orders service с Customers.return_window
- **Ссылки**: cross-domain-flows.md#Flow-3

### BR-014: Partial shipment tracking (OPEN)
- **Домен**: Orders
- **Описание**: Если заказ отправлен частично, нужно отслеживать остаток
- **Правило**: PROPOSED — нужно уточнить требования
- **Критерии тестирования**: TBD
- **Реализация**: TBD
- **Ссылки**: orders.md (OPEN вопросы)

### BR-015–BR-019: Резерво для будущих правил Orders domain

---

## Payments domain (BR-020 до BR-029)

### BR-020: PaymentAttempt is source of truth for payment status (CONFIRMED)
- **Домен**: Payments
- **Описание**: PaymentAttempt таблица — единственный источник истины для статуса платежа
- **Правило**: Никогда не читать `order.is_paid` или `invoice.is_paid`; всегда читать из `PaymentAttempt.status`
- **Критерии тестирования**:
  - ✓ Order.is_paid = null (не используется), читать PaymentAttempt вместо
  - ✗ Code использует order.is_paid вместо PaymentAttempt → code review issue
- **Реализация**: API Orders / Invoices возвращает payment_status из Payments domain
- **Ссылки**: payments.md

### BR-021: PaymentAttempt statuses (CONFIRMED)
- **Домен**: Payments
- **Описание**: PaymentAttempt может быть в одном из 5 состояний
- **Правило**: status в [PENDING, SUCCESS, FAILED, REFUNDED, CANCELLED]
- **Критерии тестирования**:
  - ✓ Новый PaymentAttempt → PENDING
  - ✓ Gateway подтвердил → SUCCESS
  - ✓ Gateway отклонил → FAILED
  - ✓ Возврат инициирован → REFUNDED
- **Реализация**: ENUM в БД, validation в service
- **Ссылки**: payments.md

### BR-022: Refund = new PaymentAttempt with type=REFUND (CONFIRMED)
- **Домен**: Payments
- **Описание**: Возврат платежа — это новый PaymentAttempt с type=REFUND
- **Правило**: Refund не изменяет исходный PaymentAttempt; создается новая запись
- **Критерии тестирования**:
  - ✓ Original PaymentAttempt.status = SUCCESS → create RefundAttempt.type = REFUND
  - ✓ Обе записи видны в audit trail
- **Реализация**: Payments service создает новый PaymentAttempt
- **Ссылки**: payments.md, cross-domain-flows.md#Flow-3

### BR-023–BR-029: Резерво для будущих правил Payments domain

---

## Invoices domain (BR-030 до BR-039)

### BR-030: Invoice.total = SUM(InvoiceLine.amount) (CONFIRMED)
- **Домен**: Invoices
- **Описание**: Сумма счета должна совпадать с суммой строк
- **Правило**: `invoice.total = SUM(line.qty * line.price - line.discount)`
- **Критерии тестирования**:
  - ✓ 3 строки по 100 + 50 = 350 → invoice.total = 350
  - ✗ invoice.total = 340 → error
- **Реализация**: Constraint в БД + validation в service
- **Ссылки**: invoices.md

### BR-031: Invoice can be paid only if not CANCELLED (PROPOSED)
- **Домен**: Invoices
- **Описание**: Отмененный счет не может быть оплачен
- **Правило**: `invoice.create_payment()` разрешена только если status != CANCELLED
- **Критерии тестирования**:
  - ✓ Invoice ISSUED → create PaymentAttempt
  - ✗ Invoice CANCELLED → create PaymentAttempt → error
- **Реализация**: Check в Invoices service
- **Ссылки**: invoices.md

### BR-032–BR-039: Резерво для будущих правил Invoices domain

---

## Purchasing domain (BR-040 до BR-049)

### BR-040: PurchaseOrder must have valid Supplier (PROPOSED)
- **Домен**: Purchasing
- **Описание**: ПО может быть создана только для существующего и активного поставщика
- **Правило**: `PurchaseOrder.supplier_id` должен существовать в Suppliers и status=ACTIVE
- **Критерии тестирования**:
  - ✓ Supplier активен → создать ПО
  - ✗ Supplier неактивен → error
- **Реализация**: FK constraint + validation
- **Ссылки**: purchasing.md

### BR-041: GoodsReceipt.qty <= PurchaseOrder.qty (PROPOSED)
- **Домен**: Purchasing
- **Описание**: Не может быть получено больше товара, чем заказано
- **Правило**: `GoodsReceipt.qty <= sum(PurchaseOrderLine.qty)`
- **Критерии тестирования**:
  - ✓ ПО на 100 шт → GoodsReceipt 100 → ok
  - ✗ ПО на 100 шт → GoodsReceipt 120 → error
- **Реализация**: Check в Purchasing service
- **Ссылки**: purchasing.md

### BR-042: GoodsReceipt.confirm → Inventory +on_hand (PROPOSED)
- **Домен**: Purchasing
- **Описание**: Подтверждение приемки товара увеличивает остаток на складе
- **Правило**: GoodsReceipt.status = CONFIRMED → Inventory RECEIPT (+on_hand)
- **Критерии тестирования**:
  - ✓ GoodsReceipt создана и подтверждена → on_hand +qty, RECEIPT запись
- **Реализация**: Async event или direct call Inventory.record_receipt()
- **Ссылки**: purchasing.md, cross-domain-flows.md#Flow-2

### BR-043–BR-049: Резерво для будущих правил Purchasing domain

---

## Customers/Suppliers domain (BR-050 до BR-069)

### BR-050: Customer.credit_limit >= 0 (PROPOSED)
- **Домен**: Customers
- **Описание**: Кредитный лимит не может быть отрицательным
- **Правило**: `credit_limit >= 0` или NULL (неограниченно)
- **Критерии тестирования**:
  - ✓ credit_limit = 1000
  - ✓ credit_limit = NULL (нет лимита)
  - ✗ credit_limit = −100 → error
- **Реализация**: Constraint в БД
- **Ссылки**: customers.md

### BR-051: Supplier.status in [ACTIVE, INACTIVE, SUSPENDED] (PROPOSED)
- **Домен**: Suppliers
- **Описание**: Поставщик может быть в одном из трех состояний
- **Правило**: status ENUM
- **Критерии тестирования**: status validation
- **Реализация**: ENUM в БД
- **Ссылки**: suppliers.md

### BR-052–BR-069: Резерво для будущих правил

---

## Warehouses domain (BR-070 до BR-079)

### BR-070: Warehouse.capacity >= SUM(on_hand on this warehouse) (PROPOSED)
- **Домен**: Warehouses
- **Описание**: Вместимость склада не может быть превышена
- **Правило**: `SUM(on_hand by sku) <= warehouse.capacity`
- **Критерии тестирования**:
  - ✓ capacity=1000, SUM(on_hand)=800 → ok
  - ✗ capacity=1000, SUM(on_hand)=1200 → warning/error
- **Реализация**: Check при RECEIPT, TRANSFER
- **Ссылки**: warehouses.md

### BR-071: WarehouseZone.type restricts operations (PROPOSED)
- **Домен**: Warehouses
- **Описание**: Тип зоны определяет допустимые операции
- **Правило**: RECEIVING zone — только приемка; STORAGE — хранение; SHIPPING — отгрузка
- **Критерии тестирования**: TBD
- **Реализация**: Check в Warehouse service
- **Ссылки**: warehouses.md

### BR-072–BR-079: Резерво

---

## Audit domain (BR-080 до BR-089)

### BR-080: All entity changes → AuditLog (CONFIRMED)
- **Домен**: Audit
- **Описание**: Все CREATE, UPDATE, DELETE операции логируются
- **Правило**: Trigger / service call перед каждой операцией
- **Критерии тестирования**:
  - ✓ Update customer name → AuditLog entry
  - ✓ Можно восстановить состояние на дату X
- **Реализация**: DB trigger или ORM hook
- **Ссылки**: audit.md

### BR-081: AuditLog is append-only (CONFIRMED)
- **Домен**: Audit
- **Описание**: AuditLog неизменяем
- **Правило**: DELETE/UPDATE AuditLog запрещен
- **Критерии тестирования**: DB constraint
- **Реализация**: Constraint + alert на попытку
- **Ссылки**: audit.md

### BR-082–BR-089: Резерво

---

## Summary таблица (по статусам)

| Статус | Кол-во | BR-xxx |
|--------|--------|--------|
| CONFIRMED | 20 | BR-001 до BR-009, BR-020-022, BR-030, BR-080-081 |
| PROPOSED | 15 | BR-010-013, BR-031-032, BR-040-043, BR-050-051, BR-070-071 |
| OPEN | 5 | BR-014, и другие в OPEN вопросах доменов |
| OUT_OF_SCOPE | – | GL, двойная запись, финансовая консолидация |

---

## Следующие шаги

- [ ] Добавить BR-023 для inventory balance reconciliation
- [ ] Определить auto-PO rules (BR-044 Purchasing)
- [ ] Spec dunning process (BR-064 Customers)
- [ ] Define multi-warehouse allocation logic (BR-072 Warehouses)
