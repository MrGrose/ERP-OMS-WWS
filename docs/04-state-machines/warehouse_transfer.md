# State Machine: WarehouseTransfer (Перемещение между складами)

## Статус
**PROPOSED**

## Диаграмма

```
DRAFT
  ↓ [confirm]
PENDING
  ↓ [goods shipped from source]
IN_TRANSIT
  ↓ [goods received at destination]
RECEIVED
  ↓ [confirm receipt]
COMPLETED → Inventory updated
  ↓ [archive]
ARCHIVED

DRAFT / PENDING
  ↓ [cancel]
CANCELLED

IN_TRANSIT
  ↓ [goods lost / variance]
VARIANCE_DETECTED
```

---

## Состояния

| Состояние | Описание | Действия |
|-----------|---------|---------|
| DRAFT | Перемещение спланировано | confirm, cancel |
| PENDING | Перемещение одобрено, товар готов к отправке | none (wait for shipment) |
| IN_TRANSIT | Товар в пути между складами | track, variance_detection |
| RECEIVED | Товар получен в целевом складе | confirm_receipt |
| COMPLETED | Перемещение завершено, остатки обновлены | none (read-only) |
| VARIANCE_DETECTED | Количество не совпадает | investigate, adjust |
| CANCELLED | Перемещение отменено | none (read-only) |
| ARCHIVED | Перемещение архивировано | none (read-only) |

---

## Переходы

### DRAFT → PENDING
**Триггер**: `transfer.confirm()`  
**Условие**: src_warehouse.available >= qty  
**Действия**:
- Reserve qty at source warehouse
- Generate transfer ticket

### PENDING → IN_TRANSIT
**Триггер**: `transfer.ship_from_source()`  
**Действия**:
- Inventory −on_hand в src (TRANSFER)
- StockMovement created
- Update tracking info

### IN_TRANSIT → RECEIVED
**Триггер**: `transfer.receive_at_destination()`  
**Действия**:
- Count items
- Compare with transfer qty

### RECEIVED → COMPLETED
**Триггер**: `transfer.confirm_receipt()` (qty matches)  
**Действия**:
- Inventory +on_hand в dst (TRANSFER)
- StockMovement created
- Transfer.status = COMPLETED

### IN_TRANSIT → VARIANCE_DETECTED
**Триггер**: Received qty ≠ expected qty  
**Действия**:
- Flag as variance
- Escalate to warehouse managers
- Investigate (loss in transit?)

### VARIANCE_DETECTED → COMPLETED
**Триггер**: Manual adjustment after investigation  
**Действия**:
- Adjust inventory accordingly
- ADJUSTMENT entry in StockMovement
- Log root cause

### (DRAFT / PENDING) → CANCELLED
**Триггер**: `transfer.cancel()`  
**Действия**:
- Release reserved items
- No inventory change

---

## OPEN вопросы

- [ ] Auto-insurance for lost shipments?
- [ ] Carrier tracking integration?
- [ ] Multi-leg transfers (A → B → C)?
