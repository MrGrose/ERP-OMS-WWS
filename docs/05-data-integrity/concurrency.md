# Целостность данных и concurrency (Data Integrity & Concurrency)

## Статус
**PROPOSED**

## Назначение
Гарантии целостности данных при параллельных операциях.

---

## Критические операции

### 1. Inventory Level Update (CONFIRMED)
**Операция**: `on_hand` и `reserved` изменяются одновременно

**Проблема**: Race condition
- Thread A: check available (100)
- Thread B: check available (100)
- Thread A: RESERVE(100) → available=0
- Thread B: RESERVE(100) → available would be −100 (invalid!)

**Решение**: 
- SELECT ... FOR UPDATE при proверке доступности
- Транзакция вся операция (RESERVE или SHIPMENT)
- Atomicity гарантирована DB лок или ORM transaction

```sql
BEGIN TRANSACTION
  SELECT on_hand, reserved FROM inventory_level WHERE sku=? FOR UPDATE
  -- Проверить available >= qty
  -- INSERT stock_movement
  UPDATE inventory_level SET reserved = reserved + qty
COMMIT
```

---

### 2. PaymentAttempt Processing (CONFIRMED)
**Проблема**: Дважды обработанный платеж

**Решение**:
- UUID (idempotency key) для каждого PaymentAttempt
- Gateway должен быть idempotent (по idempotency key)
- На запрос одного платежа — один результат (SUCCESS or FAILED)
- Retry не создает новый платеж

---

### 3. Reservation Release during Shipment (CONFIRMED)
**Проблема**: 
- Order.cancel() → RELEASE резерва
- Order.ship() → SHIPMENT (on_hand −, reserved −)
- Если происходит одновременно, может быть двойное −

**Решение**:
- Reservation.status = SHIPPED (immutable после SHIPMENT)
- Попытка RELEASE после SHIPPED → error

---

### 4. GoodsReceipt and Inventory (PROPOSED)
**Проблема**: 
- Приемка товара может быть обработана дважды

**Решение**:
- GoodsReceipt.id unique + idempotency key
- RECEIPT в stock_movement с FK на goods_receipt_id (уникальность)
- Попытка повторной приемки того же товара → error (duplicate FK)

---

## Уровни изоляции (Isolation Levels)

**Рекомендация**: READ_COMMITTED или SERIALIZABLE в зависимости от нагрузки

| Операция | Уровень | Обоснование |
|----------|---------|------------|
| Inventory RESERVE | SERIALIZABLE | Критическая целостность |
| SHIPMENT | SERIALIZABLE | Критическая целостность |
| Invoice query | READ_COMMITTED | Чтение данных, не критическое |
| Audit log INSERT | READ_UNCOMMITTED | Only INSERT, no conflicts |

---

## Оптимистичные блокировки (Optimistic Locking)

Используется для слабо конкурентных операций:
- Order.update (change details)
- Customer.update (change address)

**Механизм**:
- Таблица: `updated_at` / `version` field
- UPDATE проверяет: WHERE id=? AND version=?
- Если version не совпадает (обновлено другим потоком) → error (retry)

```python
# ORM пример (SQLAlchemy)
order.address = "new address"
order.version += 1
session.commit()  # Если version изменился кем-то еще → IntegrityError
```

---

## Dead Lock Prevention

**Правило**: Всегда блокировать таблицы в одном порядке

Если операция A блокирует (Inventory → Order), операция B должна блокировать (Inventory → Order), не (Order → Inventory)

```python
# Good: consistent lock order
with database.transaction():
    inventory_lock = db.query(InventoryLevel).filter(...).with_for_update()
    order_lock = db.query(Order).filter(...).with_for_update()

# Bad: different order (deadlock risk)
with database.transaction():
    order_lock = db.query(Order).filter(...).with_for_update()
    inventory_lock = db.query(InventoryLevel).filter(...).with_for_update()
```

---

## Event Sourcing (PROPOSED)

Для StockMovement и Orders рассмотреть Event Sourcing:
- Каждая операция = immutable event
- State (on_hand, order.status) = projection events
- Advantage: full audit trail, time-travel debugging
- Disadvantage: complexity, storage

---

## Тестовые сценарии

### Test: Concurrent RESERVE
```
Thread A: RESERVE(50) для Order 1
Thread B: RESERVE(50) для Order 2
on_hand = 100, reserved = 0

Expected:
- One thread succeeds (reserved = 50)
- Other thread fails (available < 50)
```

### Test: Concurrent SHIPMENT and CANCEL
```
Thread A: ship() → SHIPMENT (on_hand−, reserved−)
Thread B: cancel() → RELEASE (reserved−)
reserved = 50

Race:
- If A wins: on_hand−50, reserved−50 ✓
- If B wins: error (already shipped) ✓
```

### Test: Double GoodsReceipt
```
Request 1: GoodsReceipt(po_id=123, qty=100) → SUCCESS
Request 2: GoodsReceipt(po_id=123, qty=100) → ERROR (duplicate on PO)
```

---

## OPEN вопросы

- [ ] Load testing: какой уровень concurrency ожидается?
- [ ] Timeout: сколько ждать блокировку перед retry?
- [ ] Monitoring: как отслеживать deadlocks и race conditions?
- [ ] Circuit breaker: если payment gateway перегружен, как fallback?
