# State Machine: PurchaseOrder (Заказ поставщику)

## Статус
**PROPOSED**

## Диаграмма

```
DRAFT
  ↓ [confirm]
PENDING
  ↓ [supplier ships / GoodsReceipt confirm]
RECEIVED
  ↓ [invoice received and matched]
INVOICED
  ↓ [payment processed]
PAID
  ↓ [archive]
ARCHIVED

DRAFT
  ↓ [cancel]
CANCELLED

PENDING
  ↓ [cancel]
CANCELLED
```

---

## Состояния

| Состояние | Описание | Действия |
|-----------|---------|---------|
| DRAFT | ПО создана, не отправлена | confirm, cancel |
| PENDING | ПО отправлена поставщику | none (wait for goods) |
| RECEIVED | Товар получен (GoodsReceipt) | match_invoice, cancel |
| INVOICED | Счет от поставщика получен | pay, cancel |
| PAID | Поставщик оплачен | archive |
| ARCHIVED | ПО завершена | none (read-only) |
| CANCELLED | ПО отменена | none (read-only) |

---

## Переходы

### DRAFT → PENDING
**Триггер**: `po.confirm()`  
**Действия**:
- Send to supplier
- Inventory reserve (optional)

### PENDING → RECEIVED
**Триггер**: GoodsReceipt.confirm()  
**Действия**:
- Inventory: on_hand += qty (RECEIPT)
- StockMovement (type=RECEIPT)

### RECEIVED → INVOICED
**Триггер**: Supplier invoice received  
**Действия**:
- Create Invoice (type=INBOUND)
- Match PO + Invoice + GoodsReceipt (3-way match)

### INVOICED → PAID
**Триггер**: PaymentAttempt.SUCCESS  
**Действия**:
- Pay supplier
- Invoice.status = PAID

### (any) → CANCELLED
**Триггер**: `po.cancel()`  
**Действия**:
- Release any reserved inventory
- Cancel associated invoices

---

## OPEN вопросы

- [ ] Partial GoodsReceipt?
- [ ] Quality inspection stage?
- [ ] Return to supplier?
