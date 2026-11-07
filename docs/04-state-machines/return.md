# State Machine: Return (Возврат)

## Статус
**PROPOSED**

## Диаграмма

```
INITIATED
  ↓ [validate reason]
REQUESTED
  ↓ [customer ships back]
IN_TRANSIT
  ↓ [warehouse receives]
RECEIVED
  ↓ [inspect / accept]
  ├─→ ACCEPTED → Inventory +on_hand, refund process
  └─→ REJECTED → return to customer

INITIATED / REQUESTED
  ↓ [cancel]
CANCELLED
```

---

## Состояния

| Состояние | Описание | Действия |
|-----------|---------|---------|
| INITIATED | Возврат инициирован | validate, cancel |
| REQUESTED | Return request одобрен, отправлена метка доставки | none (wait for goods) |
| IN_TRANSIT | Товар в пути обратно | none (track shipment) |
| RECEIVED | Товар получен на складе | inspect, accept, reject |
| ACCEPTED | Возврат принят, товар в система | refund, none (read-only) |
| REJECTED | Возврат отклонен, товар возвращен | none (read-only) |
| CANCELLED | Возврат отменен | none (read-only) |

---

## Переходы

### INITIATED → REQUESTED
**Триггер**: `return.validate_return_request()`  
**Условие**: Within return window, valid reason  
**Действия**:
- Check return policy (BR-013)
- Generate RMA (Return Merchandise Authorization) number
- Send return label to customer

### REQUESTED → IN_TRANSIT
**Триггер**: Customer ships goods  
**Действия**:
- Track shipment (optional)

### IN_TRANSIT → RECEIVED
**Триггер**: Warehouse receives package  
**Действия**:
- Scan RMA number
- Count items

### RECEIVED → ACCEPTED
**Триггер**: `return.accept()`  
**Условие**: Quality check passed  
**Действия**:
- Inventory +on_hand (RETURN)
- StockMovement (type=RETURN)
- Create RefundInvoice (credit note)
- Initiate refund PaymentAttempt

### RECEIVED → REJECTED
**Триггер**: `return.reject()` (e.g., item damaged, outside window)  
**Действия**:
- Prepare return shipment to customer
- Return.status = REJECTED
- No inventory change
- No refund

---

## OPEN вопросы

- [ ] Restocking fee?
- [ ] Item condition check (new vs used)?
- [ ] Partial return acceptance?
