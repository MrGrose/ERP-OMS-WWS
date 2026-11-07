# State Machine: GoodsReceipt (Приемка товара)

## Статус
**PROPOSED**

## Диаграмма

```
DRAFT
  ↓ [scan items, verify]
RECEIVED (physical goods counted)
  ↓ [quality check pass / skip]
QUALITY_PASSED
  ↓ [confirm receipt]
CONFIRMED → Inventory +on_hand
  ↓ [archive]
ARCHIVED

RECEIVED
  ↓ [quality check fail]
QUALITY_FAILED
  ↓ [return to supplier / rework]
  └─→ REJECTED

DRAFT / RECEIVED
  ↓ [cancel]
CANCELLED
```

---

## Состояния

| Состояние | Описание | Действия |
|-----------|---------|---------|
| DRAFT | Приемка инициирована, товар еще не считан | scan_items |
| RECEIVED | Товар физически получен и считан | quality_check, confirm |
| QUALITY_PASSED | Товар прошел контроль качества | confirm |
| QUALITY_FAILED | Товар не прошел контроль | return, rework, reject |
| CONFIRMED | Приемка завершена, товар в системе | none (read-only) |
| REJECTED | Товар отклонен, вернут поставщику | none (read-only) |
| CANCELLED | Приемка отменена | none (read-only) |
| ARCHIVED | Приемка архивирована | none (read-only) |

---

## Переходы

### DRAFT → RECEIVED
**Триггер**: `receipt.scan_items()` (barcode scan or manual count)  
**Действия**:
- Record qty_received
- Compare with PurchaseOrder.qty

### RECEIVED → QUALITY_PASSED (skip quality check)
**Триггер**: `receipt.confirm()` without quality check  
**Действия**:
- Mark for direct confirmation

### RECEIVED → QUALITY_PASSED → CONFIRMED
**Триггер**: Quality check passed, then confirm  
**Действия**:
- Inventory +on_hand (RECEIPT)
- StockMovement created
- GoodsReceipt.status = CONFIRMED

### RECEIVED → QUALITY_FAILED
**Триггер**: Quality inspection failed  
**Действия**:
- Hold goods
- Notify supplier and purchasing team
- Escalate for decision (return / rework / partial acceptance)

### QUALITY_FAILED → REJECTED
**Триггер**: Decision to return to supplier  
**Действия**:
- Create return shipment
- Inventory: no change (товар не входил в систему)
- GoodsReceipt.status = REJECTED

---

## OPEN вопросы

- [ ] Mandatory quality check или optional?
- [ ] Partial acceptance (some items good, some reject)?
- [ ] Variance handling (received qty != PO qty)?
