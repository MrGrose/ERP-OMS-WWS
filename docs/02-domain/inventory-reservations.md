# Резервирование товара (Reservations Subsystem)

## Статус
**CONFIRMED**

## 1. Назначение
Reservations — подсистема Inventory домена. Управляет зарезервированными остатками товаров для заказов. Гарантирует, что зарезервированный товар не может быть распределен другому заказу.

## 2. Основные сущности
- **Reservation** — запись о резервировании товара для заказа
  - `id`, `order_id`, `sku`, `warehouse_id`, `qty`, `status` (ACTIVE, RELEASED, EXPIRED)
  - `created_at`, `released_at`, `expires_at`
- **InventoryLevel** — включает поле `reserved` (количество зарезервированного товара)

## 3. Основные процессы
- **RESERVE**: Orders инициирует → Inventory создает Reservation + увеличивает `reserved`
- **RELEASE**: Orders отменяет → Inventory удаляет Reservation + уменьшает `reserved`
- **SHIPMENT**: Orders отправляет → Inventory уменьшает `on_hand` И `reserved` на одно значение (резерв → отгрузка)
- **REVERT**: Возврат товара → Orders инициирует → Inventory уменьшает `reserved` (товар возвращен, заказ не нужен)

## 4. Ключевые правила

### BR-010: Резервирование не уменьшает on_hand
```
on_hand: количество физического товара на складе (не изменяется при резервировании)
reserved: количество, выделенное для конкретного заказа (может быть отменено)
available = on_hand - reserved: количество свободного товара для новых заказов
```

### BR-011: Резерв может быть отменен
- Заказ отменен → Inventory освобождает резерв (RELEASE)
- Резерв истек (expires_at пройден) → автоматическое RELEASE (если реализуемо)
- Товар возвращен → резерв снимается (REVERT)

### BR-012: Отгрузка включает снятие резерва
```
Отгрузка (SHIPMENT):
  on_hand -= qty
  reserved -= qty
  (физический товар уходит, резерв исполняется)
```

### BR-013: Невозможно зарезервировать больше, чем available
```
NEW_RESERVATION.qty <= available
// Где available = on_hand - (sum of all active reservations for this SKU on this warehouse)
```

## 5. Граница интеграции
- **Orders** инициирует: RESERVE (создание), RELEASE (отмена), SHIPMENT (исполнение)
- **Inventory** выполняет: проверка доступности, создание/удаление Reservation записи, обновление `reserved`
- **StockMovement** логирует: все операции с типом RESERVE, RELEASE, SHIPMENT

## 6. Состояния резервации
```
ACTIVE          -- создана, ожидает отгрузки
  ↓ (shipment initiates)
SHIPPED         -- товар отгружен (резерв исполнен)
  
ACTIVE
  ↓ (order cancelled)
RELEASED        -- резерв отменен, товар вернулся в available

ACTIVE
  ↓ (reservation expires)
EXPIRED         -- резерв истек (если реализуемо)
```

## 7. Примеры сценариев

### Сценарий 1: Успешная отгрузка
```
1. Order создан: qty=10, SKU=ABC
2. Orders инициирует RESERVE → Inventory.reserved += 10
   available = on_hand(50) - reserved(10) = 40
3. Orders инициирует SHIPMENT → Inventory.on_hand -= 10, Inventory.reserved -= 10
   available = on_hand(40) - reserved(0) = 40
```

### Сценарий 2: Отмена заказа
```
1. Order создан: qty=10, SKU=ABC
2. Orders инициирует RESERVE → Inventory.reserved += 10
3. Order отменен → Orders инициирует RELEASE → Inventory.reserved -= 10
   available = on_hand(50) - reserved(0) = 50 (вернулось в доступное)
```

### Сценарий 3: Частичная отгрузка
```
1. Order: qty=10, SKU=ABC
2. RESERVE: reserved += 10
3. SHIPMENT (6 шт) → on_hand -= 6, reserved -= 6
4. RELEASE (оставшиеся 4 шт) → reserved -= 4
   Финал: on_hand −6, reserved = 0 (4 не нужны)
```

## 8. Журнал и аудит
- Таблица `stock_movement` логирует все операции: RESERVE, RELEASE, SHIPMENT
- Каждая запись включает `reference_id` (order_id) для связи с заказом

## 9. OPEN вопросы
- [ ] Expiration logic: нужны ли зарезервированные товары с deadline?
- [ ] Timeout: если заказ не оплачен за N дней, автоматически освобождать резерв?
- [ ] Multi-warehouse reservation: нужна ли сложная логика выбора склада?
- [ ] Reservation versioning: нужна ли возможность изменить зарезервированное количество?
