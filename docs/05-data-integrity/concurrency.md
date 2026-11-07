# Concurrency и целостность

**Статус:** as-built Backend MVP

## Критические операции

### 1. Резервирование (Inventory)

| Аспект | Состояние |
|--------|-----------|
| `SELECT … FOR UPDATE` на `InventoryLevel` | **IMPLEMENTED** (`inventory/service.py`) |
| Атомарность reserve + movement | **IMPLEMENTED** в одной транзакции |
| Защита от overselling | **IMPLEMENTED** (insufficient available → error) |
| Integration тест гонки | **NOT VERIFIED** без PostgreSQL (`test_reserve_concurrency.py`) |

### 2. Payment webhook

| Аспект | Состояние |
|--------|-----------|
| Идемпотентность по `external_event_id` | **IMPLEMENTED** |
| `begin_nested()` при дубликате | **IMPLEMENTED** |
| Unit тест | **IMPLEMENTED** `test_payments_invoices.py` |

### 3. Частичная отгрузка / double ship

| Аспект | Состояние |
|--------|-----------|
| LIMIT по `quantity_shipped` | **IMPLEMENTED** (CHECK migration `0007`) |
| Ship вне ASSEMBLING | **IMPLEMENTED** reject |
| Unit | **IMPLEMENTED** `test_partial_ship.py` |

### 4. Double confirm order

| Аспект | Состояние |
|--------|-----------|
| Повторный confirm | **IMPLEMENTED** guard (`test_order_service` / customer tests) |

### 5. TOCTOU при reserve

| Аспект | Состояние |
|--------|-----------|
| Пре-check без блокировки убран | **IMPLEMENTED** (AUD-002 в readiness audit) |

## Разделение подтверждений

- **Код есть** — логика в `domains/*/service.py`.
- **Unit tests** — `tests/unit/*` (pytest default без integration).
- **Integration** — только при `TEST_DATABASE_URL` / marker.

## OPEN / PLANNED

- Пессимистичные локи на всём каталоге заказов — **не требуется** в MVP.
- Распределённые транзакции — **OUT OF SCOPE**.

См. также [`../02-domain/domain-map.md`](../02-domain/domain-map.md) (Inventory — единственный writer остатков).
