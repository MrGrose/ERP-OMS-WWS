# State Machine: Invoice (Счет)

## Статус
**PROPOSED**

## Диаграмма

```
DRAFT
  ↓ [issue]
ISSUED
  ↓ [receive_payment SUCCESS]
PAID
  ↓ [archive]
ARCHIVED

ISSUED
  ↓ [receive_payment FAILED / timeout]
OVERDUE

ISSUED
  ↓ [apply_credit]
PARTIALLY_PAID

DRAFT / ISSUED
  ↓ [cancel]
CANCELLED
```

---

## Состояния

| Состояние | Описание | Действия |
|-----------|---------|---------|
| DRAFT | Счет создан, не отправлен | issue, cancel |
| ISSUED | Счет выставлен | receive_payment, apply_credit, cancel |
| PAID | Счет полностью оплачен | archive, create_credit_note |
| PARTIALLY_PAID | Часть суммы получена | receive_additional_payment, cancel |
| OVERDUE | Срок оплаты прошел | escalate, cancel |
| CANCELLED | Счет отменен | none (read-only) |
| ARCHIVED | Счет завершен | none (read-only) |

---

## Переходы

### DRAFT → ISSUED
**Триггер**: `invoice.issue()`  
**Действия**: 
- Send to customer
- Create PaymentAttempt

### ISSUED → PAID
**Триггер**: PaymentAttempt.status = SUCCESS  
**Действия**:
- Update Invoice.paid_date
- Archive (optional)

### ISSUED → OVERDUE
**Триггер**: Scheduled task (due_date прошел)  
**Действия**:
- Mark as overdue
- Send reminder
- (Future: dunning process)

### ISSUED → CANCELLED
**Триггер**: `invoice.cancel()` (e.g., order cancelled)  
**Действия**:
- Cancel associated PaymentAttempt
- Release related goods (если applicable)

---

## OPEN вопросы

- [ ] Dunning process for overdue?
- [ ] Partial payment reconciliation?
- [ ] Auto-archive after 1 year?
