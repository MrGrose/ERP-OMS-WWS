# Architecture (as-built)

**Статус:** описывает репозиторий Backend MVP. **Не** включает React UI, JWT или отдельные слои `services/` / `repositories/`.

## Контекст системы

```text
Клиенты API (curl, тесты, будущий UI)
        │ HTTP + заголовки RBAC
        ▼
┌───────────────────────────────────────┐
│  FastAPI  src/erp_oms_wms/main.py     │
│  routers: src/erp_oms_wms/api/routers/ │
└───────────────────────────────────────┘
        │ вызовы функций домена
        ▼
┌───────────────────────────────────────┐
│  Domain logic                         │
│  src/erp_oms_wms/domains/<domain>/    │
│  models.py, service.py, enums, errors │
└───────────────────────────────────────┘
        │ SQLAlchemy session
        ▼
┌───────────────────────────────────────┐
│  PostgreSQL 16 (source of truth)      │
│  Alembic: alembic/versions/0001-0007  │
└───────────────────────────────────────┘

Фон: ARQ worker ← Redis ← jobs/*.py
```

Внешние системы (реальный PSP, 1С, email) в MVP **не** подключены — только заглушки и webhook endpoint.

## Слои

| Слой | Путь | Роль |
|------|------|------|
| HTTP | `api/routers/*.py`, `api/schemas.py` | Валидация запроса, RBAC, ответ |
| Домен | `domains/<name>/service.py` | Бизнес-операции, переходы статусов |
| Модели | `domains/<name>/models.py` | SQLAlchemy ORM |
| Инфраструктура | `db.py`, `worker.py`, `compose.yml` | Engine, сессии, ARQ |

HTTP-обработчики **не** содержат расчётов остатков и правил заказа — только делегируют в `service.py` того же домена (или смежного через явный вызов).

## Авторизация

**IMPLEMENTED:** `api/rbac.py`

- `X-User-Role`: `Admin` | `Manager` | `WarehouseOperator` | `Accountant`.
- Без заголовка в dev по умолчанию трактуется как `Admin` (`get_current_role`).
- `require_permission(...)` на критичных маршрутах.

JWT/OAuth **OUT OF SCOPE**.

## Домены и API (кратко)

Префиксы см. `main.py` (типично `/api/...`): catalog, warehouses, inventory, orders, invoices, payments, customers, pricing, suppliers, purchasing, transfers, returns, audit, reports.

**Inventory** — единственный writer `on_hand` / `reserved` на `InventoryLevel`. Orders инициирует reserve/ship через `inventory.service`.

## Данные и целостность

- Транзакции: `session_scope` / commit в сервисах.
- Конкуренция: `SELECT … FOR UPDATE` на уровне остатка при резерве (см. [`05-data-integrity/concurrency.md`](../05-data-integrity/concurrency.md)).
- Идемпотентность платежей: уникальный `external_event_id` + `begin_nested()` в `payments/service.py`.
- CHECK constraints: остатки, `order_line.quantity_shipped` (миграция `0007`).

## Фоновые задачи

Redis + ARQ: `worker.py` регистрирует 6 функций из `jobs/`. Расписание в compose **не** настроено — ручной enqueue или внешний scheduler. См. [`06-tech/background-jobs.md`](../06-tech/background-jobs.md).

## Что намеренно отсутствует

- Отдельные каталоги `src/services/`, `src/repositories/`.
- Frontend.
- Event bus / CQRS — синхронные вызовы сервисов в одной БД.

## Связанные документы

- [`../02-domain/domain-map.md`](../02-domain/domain-map.md)
- [`../05-data-integrity/concurrency.md`](../05-data-integrity/concurrency.md)
- [`../06-tech/background-jobs.md`](../06-tech/background-jobs.md)
