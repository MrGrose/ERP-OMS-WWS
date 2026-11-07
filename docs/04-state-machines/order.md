# State Machine: Order (Заказ)

## Статус
**CONFIRMED**

## Назначение
Описание всех возможных состояний заказа и переходов между ними.

---

## Диаграмма состояний

```
DRAFT
  ↓ [confirm] / RESERVE товар
PENDING  ←─────────────┐
  ↓ [receive_payment]  │
CONFIRMED              │
  ↓ [ship] / −on_hand  │
SHIPPED                │
  ↓ [deliver]          │
DELIVERED              │
  ↓ [archive]          │
ARCHIVED               │
                       │
CANCELLED ←────────────┤
  [cancel from DRAFT/  │
   PENDING]            │
                       │
FAILED ←─────────────────── [payment/inventory error]

RETURNED
  [full return after DELIVERED]
```

---

## Таблица состояний

| Состояние | Описание | Возможные действия | Инварианты |
|-----------|---------|-------------------|-----------|
| **DRAFT** | Заказ создан, не подтвержден | confirm, cancel, delete | no reservation, no invoice |
| **PENDING** | Ожидание подтверждения платежа | confirm (при платеже), cancel | reservation active, inventory locked |
| **CONFIRMED** | Заказ подтвержден и оплачен | ship, return | reserved товар выделен, invoice issued |
| **SHIPPED** | Товар отправлен | deliver, receive_return | on_hand уменьшен, reserved освобожден |
| **DELIVERED** | Товар доставлен | return (в пределах return window), archive | customer has goods |
| **ARCHIVED** | Заказ завершен | none | read-only, история сохранена |
| **CANCELLED** | Заказ отменен | none (можно создать новый) | reservation released, invoice cancelled |
| **FAILED** | Ошибка (платеж, сток) | retry or cancel | depends on failure reason |
| **RETURNED** | Товар полностью возвращен | archive | inventory restored, refund processed |

---

## Переходы и триггеры

### DRAFT → PENDING
**Триггер**: `order.confirm()`  
**Действия**:
- Проверить Inventory.available >= sum(OrderLine.qty)
- Инициировать RESERVE в Inventory (каждой позиции)
- Создать Invoice (тип OUTBOUND)
- Создать PaymentAttempt

**Постусловия**: 
- Order.status = PENDING
- Inventory.reserved += qty для каждой позиции
- Invoice.status = ISSUED
- PaymentAttempt.status = PENDING

---

### PENDING → CONFIRMED
**Триггер**: PaymentAttempt.status = SUCCESS (event from Payments)  
**Действия**:
- Обновить Order.status = CONFIRMED
- Invoice.status = PAID
- (Warehouse может начать подготовку отгрузки)

**Постусловия**:
- Order.status = CONFIRMED
- Payment успешен

---

### PENDING → FAILED
**Триггер**: PaymentAttempt.status = FAILED (payment gateway error)  
**Действия**:
- Order.status = FAILED
- Release RESERVE в Inventory
- Invoice.status = FAILED

**Постусловия**:
- Inventory.reserved -= qty (товар вернулся в доступное)
- Customer может retry платеж

---

### DRAFT → CANCELLED
**Триггер**: `order.cancel()`  
**Допустимо из**: DRAFT только  
**Действия**: 
- Удалить неиспользованные Invoice/PaymentAttempt
- Order.status = CANCELLED

**Постусловия**:
- Никаких изменений inventory (еще не было RESERVE)

---

### PENDING → CANCELLED
**Триггер**: `order.cancel()`  
**Допустимо из**: PENDING  
**Действия**:
- Release RESERVE в Inventory: reserved -= qty
- Cancel Invoice
- Cancel PaymentAttempt (если PENDING)

**Постусловия**:
- Order.status = CANCELLED
- Inventory.reserved -= qty (вернулось в доступное)
- Invoice.status = CANCELLED

---

### CONFIRMED → SHIPPED
**Триггер**: `order.ship()` (from Warehouse/Fulfillment)  
**Действия**:
- Create Shipment record
- Inventory: on_hand -= qty, reserved -= qty (SHIPMENT)
- Отправить товар (track & trace)
- Update Order.tracking_number

**Постусловия**:
- Order.status = SHIPPED
- Inventory.on_hand уменьшен
- StockMovement (type=SHIPMENT) создан

---

### SHIPPED → DELIVERED
**Триггер**: `order.deliver()` (when customer confirms receipt)  
**Действия**:
- Update delivery_date
- Order.status = DELIVERED

**Постусловия**:
- Order.status = DELIVERED
- Return window starts (если есть return_policy)

---

### DELIVERED → ARCHIVED
**Триггер**: `order.archive()` (manual or automatic after 90 days)  
**Действия**:
- Move to archive table (optional)
- Order.status = ARCHIVED
- Mark invoice as reconciled (if paid)

**Постусловия**:
- Order becomes read-only
- History preserved for audit

---

### DELIVERED → RETURNED (или SHIPPED → RETURNED)
**Триггер**: `order.return_goods()` (customer initiates return)  
**Условие**: Within return window (BR-013)  
**Действия**:
- Create Return record
- Warehouse receives goods back (GoodsReceipt type=RETURN)
- Inventory: on_hand += qty (RETURN)
- Create RefundInvoice (credit note)
- Initiate PaymentAttempt type=REFUND

**Постусловия**:
- Order.status = RETURNED
- Inventory.on_hand restored
- Refund processed

---

### CONFIRMED → FAILED (Inventory issue during shipment prep)
**Триггер**: Inventory check failed (stock reserved but can't be located)  
**Действия**:
- Set Order.status = FAILED
- Escalate to warehouse manager
- Option: Release RESERVE and refund, or hold for investigation

**Постусловия**:
- Requires manual intervention

---

## OPEN вопросы

- [ ] Partial shipment: нужен ли intermediate state (PARTIALLY_SHIPPED)?
- [ ] Return from SHIPPED vs DELIVERED: разные rules?
- [ ] Hold for review: нужен ли state для fraud/credit checks?
- [ ] Timeout: автоматический CANCELLED если PENDING более N дней?
- [ ] Backorder: если stock недоступен, создавать backorder state или FAILED?

---

## Правила валидации

- Переход возможен только из состояний, указанных выше
- Попытка неверного перехода → error (не UPDATE напрямую status)
- Все переходы должны логироваться в audit_log

---

## Тестовые сценарии

### Test 1: Happy path
```
DRAFT → confirm() → PENDING → payment SUCCESS → CONFIRMED → ship() → SHIPPED → deliver() → DELIVERED → archive() → ARCHIVED
```

### Test 2: Cancelled at DRAFT
```
DRAFT → cancel() → CANCELLED
```

### Test 3: Cancelled at PENDING
```
DRAFT → confirm() → PENDING → cancel() → CANCELLED
Check: Inventory.reserved -= qty
```

### Test 4: Payment failed
```
DRAFT → confirm() → PENDING → payment FAILED → FAILED
Check: Inventory.reserved -= qty, Invoice cancelled
```

### Test 5: Return
```
... → DELIVERED → return_goods() → RETURNED
Check: Inventory +on_hand, refund processed
```
