# Домен: Inventory (Остатки)

## Статус
**CONFIRMED**

## 1. Назначение и граница домена
Управление остатками товаров на всех складах. Inventory — единственный writer для полей `on_hand`, `reserved`, `available`. Отслеживание доступности товара для заказов и операций планирования закупок.

## 2. Основные сущности
- **InventoryItem** — SKU, название, единица измерения, категория
- **InventoryLevel** — остаток на конкретном складе (warehouse_id, sku, on_hand, reserved, available)
- **InventoryHistory** / **InventoryAuditLog** — трассировка всех изменений остатков

Вычисляемое поле:
```
available = on_hand - reserved
```

## 3. Основные процессы
- **Приемка товара** (RECEIPT): Purchasing → Inventory, `on_hand` +
- **Отгрузка** (SHIPMENT): Orders → Inventory, `on_hand` −
- **Резервирование** (RESERVE): Orders инициирует, Inventory создает резерв, `reserved` +
- **Освобождение резерва** (RELEASE): Orders отменяет, Inventory освобождает резерв, `reserved` −
- **Перемещение между складами** (TRANSFER): `on_hand` перемещается между локациями
- **Инвентаризация** (RECOUNT): Корректировка по факту, с обоснованием (WRITE_OFF, ADJUSTMENT)

## 4. Граница интеграции

**Входящие:**
- **Purchasing** → приемка товара (GoodsReceipt) → Inventory +on_hand + StockMovement RECEIPT
- **Orders** → инициирует резервирование → Inventory создает резерв (+reserved)
- **Orders** → инициирует отгрузку → Inventory −on_hand + StockMovement SHIPMENT
- **Warehouses** → локации (список складов) для multi-warehouse поддержки

**Исходящие:**
- → **Orders**: проверка доступности (available ≥ заказ.qty)
- → **Purchasing**: сигнал для автоматического заказа (если on_hand < reorder_point)
- → **StockMovement**: каждое изменение остатка записывается с обоснованием

## 5. Инварианты и правила
- **BR-001**: `on_hand` ≥ 0 всегда
- **BR-002**: `reserved` ≤ `on_hand` (зарезервировано не может быть больше доступного)
- **BR-003**: `available = on_hand - reserved`, вычисляется, не хранится
- **BR-004**: Любое изменение остатка — только через StockMovement с типом (RECEIPT, SHIPMENT, TRANSFER, ADJUSTMENT, WRITE_OFF, RECOUNT, RETURN)
- **BR-005**: Резервирование не уменьшает `on_hand`; отгрузка — отдельная операция
- **BR-006**: Резерв может быть отменен (RELEASE) только если заказ отменен или возвращен

## 6. Состояния и переходы
Inventory уровень не имеет state machine (это просто числа). Но операции StockMovement имеют состояния:
- Детали в `docs/04-state-machines/stock_movement.md` (PROPOSED)

## 7. Журнал и аудит
Все изменения остатков записываются в **StockMovement** журнал:
- **Кто изменил** (user_id, service_id)
- **Что изменилось** (sku, warehouse_id, old_on_hand, new_on_hand, delta)
- **Когда** (timestamp)
- **Почему** (reason: RECEIPT, SHIPMENT, TRANSFER, ADJUSTMENT, WRITE_OFF, RECOUNT, RETURN)
- **Обоснование** (reference_id: purchase_order_id, order_id, transfer_id, adjustment_note, etc.)

## 8. Интеграция с другими доменами
- **Order → Reservation flow**: Orders инициирует резерв → Inventory резервирует → StockMovement логирует RESERVE
- **GoodsReceipt → Inventory flow**: Purchasing подтверждает прием → Inventory +on_hand + StockMovement RECEIPT
- **Shipment → Inventory flow**: Orders отправляет → Inventory −on_hand + StockMovement SHIPMENT (+ RELEASE резерва)
- **Transfer between warehouses**: Warehouse инициирует перемещение → Inventory TRANSFER (−on_hand в src, +on_hand в dst)
- Детальные flows в `docs/02-domain/cross-domain-flows.md`

## 9. OPEN вопросы и риски
- [ ] Multi-warehouse логика: нужна ли сложная логика распределения по складам или простое округление?
- [ ] Reorder point logic: автоматические заказы или ручное планирование?
- [ ] Stock valuation method: FIFO, LIFO, weighted average? (вероятно, OUT_OF_SCOPE, но нужно уточнить)
- [ ] Lot/Serial tracking: требуется ли отслеживание по партиям или серийным номерам? (PROPOSED)
- [ ]损 (WRITE_OFF): процесс и требования утверждения?
