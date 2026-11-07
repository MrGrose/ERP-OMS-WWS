# State Machine: Reservation (Резервирование)

## Статус
**CONFIRMED**

## Диаграмма

```
ACTIVE (创建时)
  ↓ [shipment initiates]
  └─→ SHIPPED (reserved → executed)

ACTIVE
  ↓ [order cancelled / expired]
  └─→ RELEASED (reserved → freed)

ACTIVE
  ↓ [partial shipment]
  └─→ PARTIALLY_SHIPPED (part executed, part released)
```

---

## Состояния

| Состояние | Описание | Действия |
|-----------|---------|---------|
| ACTIVE | Резерв активен, товар выделен | ship, release, partial_ship |
| SHIPPED | Резерв исполнен (товар отправлен) | none (read-only) |
| RELEASED | Резерв освобожден (заказ отменен) | none (read-only) |
| PARTIALLY_SHIPPED | Часть отправлена, остаток освобожден | none (read-only) |

---

## Переходы

### ACTIVE → SHIPPED
**Триггер**: Order.ship() executes reservation  
**Действия**:
- Inventory: on_hand -= qty, reserved -= qty
- StockMovement (type=SHIPMENT)
- Reservation.status = SHIPPED

### ACTIVE → RELEASED
**Триггер**: Order.cancel() or reservation expires  
**Действия**:
- Inventory: reserved -= qty
- StockMovement (type=RELEASE)
- Reservation.status = RELEASED

### ACTIVE → PARTIALLY_SHIPPED
**Триггер**: Partial shipment  
**Действия**:
- Inventory: on_hand -= shipped_qty, reserved -= shipped_qty
- Create new Reservation for released_qty with status=RELEASED
- Current Reservation.status = PARTIALLY_SHIPPED

---

## OPEN вопросы

- [ ] Expiration: auto-RELEASE если reservation старше N дней?
- [ ] Multi-warehouse: как выбирать склад для резерва?
