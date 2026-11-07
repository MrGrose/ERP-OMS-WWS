# Семантика движений товара (Stock Movement Types)

## Статус
**CONFIRMED**

## Назначение
Таблица `stock_movement` — журнал всех операций, которые изменяют `on_hand`, `reserved` или статус резервов. Каждая запись — grund (основание) и аудит-трейл для проверки целостности остатков.

---

## Таблица: 7 типов движений

| Тип | Направление | Поле | Что изменяется | Кто инициирует | Ссылка | BR |
|-----|-------------|------|---|---|---|---|
| **RECEIPT** | Входящее | `on_hand` | +qty | Purchasing (GoodsReceipt) | purchase_order_id | BR-004 |
| **SHIPMENT** | Исходящее | `on_hand`, `reserved` | −qty on_hand, −qty reserved | Orders (shipment) | order_id, shipment_id | BR-004, BR-010 |
| **TRANSFER** | Внутреннее | `on_hand` | −qty в src_warehouse, +qty в dst_warehouse | Warehouses | transfer_id | BR-004 |
| **RESERVE** | Резервирование | `reserved` | +qty | Orders (новый заказ) | order_id, reservation_id | BR-010, BR-013 |
| **RELEASE** | Отмена резерва | `reserved` | −qty | Orders (отмена/возврат) | order_id, reservation_id | BR-011 |
| **ADJUSTMENT** | Корректировка | `on_hand` | ±qty | Warehouse/Inventory (инвентаризация) | adjustment_id, reason_note | BR-004 |
| **WRITE_OFF** | Списание | `on_hand` | −qty | Inventory/Warehouse (потеря/брак) | write_off_id, reason_note | BR-004 |
| **RETURN** | Возврат | `on_hand`, `reserved` | +qty on_hand, −qty reserved | Orders (возврат товара) | order_id, return_id | BR-004, BR-011 |

---

## Детальное описание каждого типа

### 1. RECEIPT — Приемка товара
**Источник:** Purchasing domain (GoodsReceipt подтвержден)

**Операция:**
```
InventoryLevel.on_hand += qty
StockMovement запись:
  type: RECEIPT
  warehouse_id: склад приемки
  sku: товар
  qty: +N
  reference_id: purchase_order_id
  user_id: кто принял
  timestamp: когда
  notes: "Приемка ПО #123"
```

**Правило:** BR-004 (любое изменение остатка = запись в журнал)

---

### 2. SHIPMENT — Отгрузка заказа
**Источник:** Orders domain (Order confirmed, shipment initiated)

**Операция:**
```
InventoryLevel.on_hand -= qty
InventoryLevel.reserved -= qty  // Резерв исполняется
StockMovement записи (2 строки или 1?):
  type: SHIPMENT
  warehouse_id: склад отправки
  sku: товар
  qty: −N
  reference_id: order_id
  shipment_id: связь с отгрузкой
  user_id: кто отправил
  timestamp: когда
  notes: "Отгрузка заказа #456"
```

**Правило:** BR-004, BR-010, BR-012 (отгрузка включает освобождение резерва)

**OPEN:** Нужны ли 2 отдельные записи (SHIPMENT + RELEASE) или одна комбинированная?

---

### 3. TRANSFER — Перемещение между складами
**Источник:** Warehouses domain (internal warehouse move)

**Операция:**
```
InventoryLevel[src_warehouse].on_hand -= qty
InventoryLevel[dst_warehouse].on_hand += qty
StockMovement записи (2 строки):
  type: TRANSFER
  warehouse_id: src_warehouse (−)
  sku: товар
  qty: −N
  reference_id: transfer_id
  
  type: TRANSFER
  warehouse_id: dst_warehouse (+)
  sku: товар
  qty: +N
  reference_id: transfer_id
```

**Правило:** BR-004

---

### 4. RESERVE — Резервирование для заказа
**Источник:** Orders domain (Order created/confirmed)

**Операция:**
```
InventoryLevel.reserved += qty
Reservation запись создана (status=ACTIVE)
StockMovement запись:
  type: RESERVE
  warehouse_id: склад для резерва
  sku: товар
  qty: +N (в reserved)
  reference_id: order_id
  reservation_id: связь
  user_id: система или пользователь
  timestamp: когда
  notes: "Резерв заказа #456"
```

**Правило:** BR-013 (проверить: available >= qty)

---

### 5. RELEASE — Освобождение резерва
**Источник:** Orders domain (Order cancelled / returned / expired)

**Операция:**
```
InventoryLevel.reserved -= qty
Reservation запись обновлена (status=RELEASED)
StockMovement запись:
  type: RELEASE
  warehouse_id: склад резерва
  sku: товар
  qty: −N (в reserved)
  reference_id: order_id
  reservation_id: связь
  user_id: система или пользователь
  timestamp: когда
  reason: CANCELLED / RETURNED / EXPIRED
  notes: "Отмена резерва заказа #456"
```

**Правило:** BR-011

---

### 6. ADJUSTMENT — Корректировка (Инвентаризация)
**Источник:** Warehouse / Inventory domain (manual recount)

**Операция:**
```
InventoryLevel.on_hand += delta  // delta может быть отрицательным
StockMovement запись:
  type: ADJUSTMENT
  warehouse_id: склад
  sku: товар
  qty: delta (может быть − или +)
  reference_id: adjustment_id
  user_id: кто провел инвентаризацию
  timestamp: когда
  reason: "Плановая инвентаризация" / "Пересчет"
  notes: "по факту N единиц против системе М"
```

**Правило:** BR-004, требует обоснования

---

### 7. WRITE_OFF — Списание (Брак, потеря)
**Источник:** Warehouse / Inventory domain (damaged goods, theft, expiry)

**Операция:**
```
InventoryLevel.on_hand -= qty  // Только −, не +
StockMovement запись:
  type: WRITE_OFF
  warehouse_id: склад
  sku: товар
  qty: −N
  reference_id: write_off_id
  user_id: кто списал
  timestamp: когда
  reason: DAMAGED / LOST / EXPIRED / OTHER
  notes: "Брак выявлен при инвентаризации"
```

**Правило:** BR-004, требует одобрения (OPEN)

---

### 8. RETURN — Возврат товара
**Источник:** Orders domain (Return initialized)

**Операция:**
```
InventoryLevel.on_hand += qty
InventoryLevel.reserved -= qty  // Если заказ еще в резерве (нештатный случай)
StockMovement записи:
  type: RETURN
  warehouse_id: склад возврата
  sku: товар
  qty: +N
  reference_id: order_id
  return_id: связь
  user_id: кто принял возврат
  timestamp: когда
  notes: "Возврат товара заказа #456"
```

**Правило:** BR-004, BR-011

---

## Таблица stock_movement (структура)

```sql
CREATE TABLE stock_movement (
  id UUID PRIMARY KEY,
  warehouse_id UUID NOT NULL,
  sku VARCHAR(50) NOT NULL,
  type ENUM(RECEIPT, SHIPMENT, TRANSFER, RESERVE, RELEASE, ADJUSTMENT, WRITE_OFF, RETURN) NOT NULL,
  qty_delta INT NOT NULL,  -- может быть − или +
  reference_id UUID,  -- purchase_order_id / order_id / transfer_id / adjustment_id / write_off_id / return_id
  reason VARCHAR(100),  -- CANCELLED, RETURNED, EXPIRED, DAMAGED, LOST, etc.
  notes TEXT,
  user_id UUID,
  created_at TIMESTAMP NOT NULL,
  
  -- Связи для трассировки
  purchase_order_id UUID,
  order_id UUID,
  shipment_id UUID,
  reservation_id UUID,
  return_id UUID,
  
  FOREIGN KEY (warehouse_id) REFERENCES warehouse(id),
  FOREIGN KEY (order_id) REFERENCES order(id),
  FOREIGN KEY (purchase_order_id) REFERENCES purchase_order(id),
  -- ... другие FK
);

CREATE INDEX idx_stock_movement_sku_warehouse ON stock_movement(sku, warehouse_id, created_at);
CREATE INDEX idx_stock_movement_order ON stock_movement(order_id);
```

---

## Валидация целостности

После каждой операции:
```
SUM(all on_hand by SKU) >= 0
SUM(reserved by SKU) <= SUM(on_hand by SKU)
available = on_hand - reserved >= 0
```

Если нарушено → error, не коммитить операцию.

---

## OPEN вопросы
- [ ] TRANSFER: нужна ли авторизация утверждения для больших перемещений?
- [ ] ADJUSTMENT/WRITE_OFF: нужно ли одобрение перед исполнением?
- [ ] SHIPMENT + RELEASE: две отдельные записи или одна комбинированная?
- [ ] Компенсация: как отменить неправильную операцию (можно ли создать −RECEIPT вместо ADJUSTMENT)?
- [ ] Массовые операции: нужна ли батч-обработка для больших перемещений?
