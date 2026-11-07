# Сценарии взаимодействия доменов (Cross-Domain Flows)

## Назначение
Описание 6 главных бизнес-процессов, затрагивающих несколько доменов. Каждый сценарий — 10 полей.

---

## Flow 1: Заказ покупателем (Order to Shipment)

| Поле | Значение |
|------|----------|
| **Название** | Заказ → Резервирование → Отгрузка |
| **Домены** | Orders, Inventory (Reservations), Payments, Invoices |
| **Триггер** | Order creation |
| **Шаги** | 1. Customer создает Order (OrderLine: qty, sku)<br>2. Orders проверяет Inventory.available >= qty<br>3. Orders инициирует Inventory.RESERVE (qty → reserved)<br>4. Orders создает Invoice<br>5. Invoices инициирует PaymentAttempt<br>6. PaymentAttempt успешен → Invoice.PAID<br>7. Orders инициирует Shipment<br>8. Inventory: on_hand −= qty, reserved −= qty (SHIPMENT)<br>9. Warehouse отправляет товар<br>10. Order.status = SHIPPED |
| **Предусловия** | Customer.credit_limit >= Order.total |
| **Постусловия** | Inventory.on_hand уменьшен, PaymentAttempt.SUCCESS |
| **Исключения** | Inventory.available < qty → Order.FAILED<br>PaymentAttempt.FAILED → escalation |
| **Ответственные домены** | Orders (главный), Inventory, Payments |
| **Журнал** | OrderStatusChange, StockMovement (RESERVE, SHIPMENT), PaymentAttempt |
| **OPEN вопросы** | Partial shipment? Backorder if stock unavailable? |

---

## Flow 2: Закупка у поставщика (Purchase Order to Goods Receipt)

| Поле | Значение |
|------|----------|
| **Название** | ПО → Приемка → Счет поставщика → Оплата |
| **Домены** | Purchasing, Inventory, Invoices, Payments, Suppliers |
| **Триггер** | Inventory.reorder_point достигнут или Manual PO creation |
| **Шаги** | 1. Inventory sends signal: on_hand < reorder_point<br>2. Purchasing создает PurchaseOrder (Supplier, qty)<br>3. Purchasing отправляет ПО поставщику<br>4. Supplier отправляет товар<br>5. Warehouse получает GoodsReceipt<br>6. GoodsReceipt.confirm → Inventory +on_hand (RECEIPT)<br>7. Supplier отправляет Invoice<br>8. Invoices создает запись (type=INBOUND)<br>9. Invoices инициирует PaymentAttempt<br>10. Payments обрабатывает оплату поставщику |
| **Предусловия** | Supplier активен, PurchaseOrder.qty > 0 |
| **Постусловия** | Inventory.on_hand увеличен, Supplier счет оплачен |
| **Исключения** | GoodsReceipt.qty != PO.qty → variance<br>Supplier invoice не совпадает с GoodsReceipt → escalation |
| **Ответственные домены** | Purchasing (главный), Inventory, Invoices |
| **Журнал** | PurchaseOrder status, StockMovement (RECEIPT), Invoice status, PaymentAttempt |
| **OPEN вопросы** | Auto-PO по reorder_point? Quality inspection перед приемкой? |

---

## Flow 3: Возврат товара (Customer Return)

| Поле | Значение |
|------|----------|
| **Название** | Возврат товара → Восстановление остатка → Возврат платежа |
| **Домены** | Orders, Inventory, Payments, Invoices |
| **Триггер** | Customer инициирует возврат товара |
| **Шаги** | 1. Customer создает Return request<br>2. Orders.status = RETURN_INITIATED<br>3. Warehouse получает товар обратно<br>4. GoodsReceipt type=RETURN<br>5. Inventory +on_hand (RETURN + уменьшить reserved если еще зарезервирован)<br>6. Orders создает RefundInvoice (credit note)<br>7. Invoices.status = CREDITED<br>8. Payments инициирует refund PaymentAttempt<br>9. PaymentAttempt.type = REFUND → Customer получает деньги<br>10. Order.status = RETURNED |
| **Предусловия** | Order.status в [SHIPPED, DELIVERED], Return reason valid |
| **Постусловия** | Inventory.on_hand восстановлен, Refund processed |
| **Исключения** | Return window закрыт → reject<br>Товар поврежден → partial refund |
| **Ответственные домены** | Orders (главный), Inventory, Payments |
| **Журнал** | Return, StockMovement (RETURN), PaymentAttempt (REFUND) |
| **OPEN вопросы** | Return inspection? Restocking fee? |

---

## Flow 4: Перемещение товара между складами (Warehouse Transfer)

| Поле | Значение |
|------|----------|
| **Название** | Перемещение товара между складами |
| **Домены** | Warehouses, Inventory, (Audit) |
| **Триггер** | Manual transfer request или automatic rebalancing |
| **Шаги** | 1. Warehouse инициирует Transfer (src, dst, sku, qty)<br>2. Inventory проверяет src.available >= qty<br>3. Transfer.status = IN_TRANSIT<br>4. Inventory.on_hand −= qty в src (TRANSFER)<br>5. Inventory.on_hand += qty в dst (TRANSFER)<br>6. Warehouse подтверждает прием в dst<br>7. Transfer.status = COMPLETED<br>8. Inventory уровни финализированы<br>9. StockMovement логирует обе операции (−qty src, +qty dst)<br>10. Audit логирует перемещение |
| **Предусловия** | src_warehouse.available >= qty, dst_warehouse.capacity >= +qty |
| **Постусловия** | Inventory.on_hand перемещены, обе локации обновлены |
| **Исключения** | Transfer in transit lost → variance detection<br>Capacity exceeded → reject |
| **Ответственные домены** | Warehouses (главный), Inventory |
| **Журнал** | Transfer status, StockMovement (2 записи: TRANSFER) |
| **OPEN вопросы** | Auto-rebalancing logic? |

---

## Flow 5: Инвентаризация и корректировка (Physical Inventory Count)

| Поле | Значение |
|------|----------|
| **Название** | Физический пересчет → Корректировка остатков |
| **Домены** | Warehouses, Inventory, (Audit) |
| **Триггер** | Scheduled inventory count или variance detected |
| **Шаги** | 1. Warehouse инициирует physical count<br>2. Warehouse записывает фактическое кол-во (phys_qty)<br>3. System вычисляет variance = system_qty − phys_qty<br>4. Если variance < tolerance → WRITE_OFF или GAIN<br>5. Inventory.on_hand корректируется на variance<br>6. StockMovement логирует ADJUSTMENT с reason_note<br>7. Audit логирует variance (кто, когда, сколько)<br>8. Если large variance → escalation для investigation<br>9. Reconciliation завершена<br>10. Next count schedule |
| **Предусловия** | Count authorized, all items counted |
| **Постусловия** | Inventory.on_hand совпадает с physical count |
| **Исключения** | Large variance (> threshold) → investigation required<br>Item missing → WRITE_OFF |
| **Ответственные домены** | Warehouses (главный), Inventory |
| **Журнал** | Physical count, StockMovement (ADJUSTMENT/WRITE_OFF), Audit variance |
| **OPEN вопросы** | Tolerance level? Investigation process? |

---

## Flow 6: Выставление и оплата счета (Invoice to Payment)

| Поле | Значение |
|------|----------|
| **Название** | Счет → Платеж → Reconciliation |
| **Домены** | Invoices, Payments, (Orders или Purchasing) |
| **Триггер** | Invoice.status = ISSUED |
| **Шаги** | 1. Invoices создает Invoice (для Order или ПО)<br>2. Invoice отправляется Customer или Supplier<br>3. Invoice.status = ISSUED, due_date = today + terms<br>4. Payments создает PaymentAttempt (Invoice.id)<br>5. PaymentAttempt отправляется в payment gateway<br>6. Gateway обрабатывает платеж (card/transfer/etc)<br>7. PaymentAttempt.status = SUCCESS/FAILED<br>8. Если SUCCESS → Invoice.status = PAID<br>9. Если FAILED → PaymentAttempt.status = FAILED, retry или escalation<br>10. Audit логирует платеж, Invoice archived при полной оплате |
| **Предусловия** | Invoice.total > 0, valid Payment Method |
| **Постусловия** | PaymentAttempt.SUCCESS, Invoice.PAID |
| **Исключения** | Payment declined → retry with different method<br>Invoice overdue → dunning process (OPEN)<br>Partial payment → multi-attempt (OPEN) |
| **Ответственные домены** | Payments (главный), Invoices |
| **Журнал** | PaymentAttempt (attempts log), Invoice status change |
| **OPEN вопросы** | Retry strategy? Dunning process? Multi-part payments? |

---

## Summary таблица

| Flow | Домены (главный) | Триггер | Результат |
|------|------------------|---------|-----------|
| 1. Order → Shipment | Orders (O, I, P) | Customer order | SHIPPED, payment processed |
| 2. PO → GoodsReceipt | Purchasing (I, P) | reorder_point | Inventory +, supplier paid |
| 3. Return | Orders (I, P) | Return initiated | Refund processed, inventory restored |
| 4. Warehouse Transfer | Warehouses (I) | Transfer request | Inventory moved between warehouses |
| 5. Physical Count | Warehouses (I) | Scheduled count | Inventory corrected by variance |
| 6. Invoice → Payment | Payments (I) | Invoice issued | Payment processed, invoice marked PAID |

(O = Orders, I = Inventory, P = Payments)

---

## Примечания

- **CONFIRMED**: Flows 1, 3, 4, 6 (Orders, Inventory, Payments)
- **PROPOSED**: Flows 2, 5 (Purchasing, Warehouses)
- **OPEN**: Dunning, retry strategies, partial payments

Все flows используют **StockMovement** как журнал и **AuditLog** как полный трейл.
