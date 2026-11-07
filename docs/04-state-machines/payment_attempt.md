# State Machine: PaymentAttempt (Попытка платежа)

## Статус
**CONFIRMED**

## Диаграмма

```
PENDING
  ↓ [gateway response]
  ├─→ SUCCESS → (archive)
  ├─→ FAILED → (retry or escalate)
  └─→ CANCELLED

FAILED
  ↓ [retry with different method / more funds]
PENDING (repeat)

SUCCESS
  ↓ [customer requests refund]
REFUND_REQUESTED
  ↓ [process refund]
  ├─→ REFUNDED (new PaymentAttempt type=REFUND created)
  └─→ REFUND_FAILED
```

---

## Состояния

| Состояние | Описание | Действия |
|-----------|---------|---------|
| PENDING | Ожидание результата от шлюза | none (wait for gateway) |
| SUCCESS | Платеж успешен | none (read-only) |
| FAILED | Платеж отклонен | retry, escalate, cancel |
| REFUNDED | Возврат обработан | none (read-only) |
| REFUND_FAILED | Возврат не удался | retry, escalate |
| CANCELLED | Платеж отменен | none (read-only) |

---

## Переходы

### PENDING → SUCCESS
**Триггер**: Payment gateway callback  
**Действия**:
- Update Invoice.status = PAID
- Update Order.status = CONFIRMED (if applicable)

### PENDING → FAILED
**Триггер**: Payment gateway callback (decline)  
**Действия**:
- Log error from gateway
- Send notification to customer
- Option: auto-retry with different method

### SUCCESS → REFUND_REQUESTED
**Триггер**: `payment.request_refund()`  
**Действия**:
- Create new PaymentAttempt type=REFUND
- Send to gateway

### REFUND_REQUESTED → REFUNDED
**Триггер**: Gateway confirms refund  
**Действия**:
- Update original PaymentAttempt.status = REFUNDED
- Create credit note in Invoice (type=CREDIT)

---

## OPEN вопросы

- [ ] Auto-retry logic for FAILED?
- [ ] Timeout for PENDING (e.g., after 24h)?
- [ ] Partial refund support?
- [ ] PCI compliance logging (mask card details)?
