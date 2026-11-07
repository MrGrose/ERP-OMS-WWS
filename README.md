# ERP-OMS-WMS

**ERP-OMS-WMS** — backend MVP, в котором в одном сервисе сходятся три слоя операционного ПО:

- **ERP (Enterprise Resource Planning)** — master data, закупки, ценообразование, поставщики, операционная отчётность.
- **OMS (Order Management System)** — заказы клиентов: черновик → резерв → счёт → оплата → отгрузка.
- **WMS (Warehouse Management System)** — остатки, резервы, движения, приёмка, перемещения и возвраты по складам.

Одна схема PostgreSQL, явные state machines и правило: **Inventory** — единственный writer полей `on_hand` и `reserved`; заказы и платежи вызывают inventory-сервисы, а не пишут остатки напрямую.

---

## О проекте

Каталог, клиентские прайс-листы, закупки у поставщиков, заказы, счета, webhook оплаты и складские эффекты (резерв, отгрузка, приёмка, transfer) собраны в одном репозитории — путь **quote-to-cash** вместе со складом.

- **Границы транзакций** в domain services (не «тонкий CRUD»).
- **Конкурентный резерв** последней единицы (integration-тесты на PostgreSQL).
- **Идемпотентные payment webhook** и истечение счёта с освобождением резерва.
- **Миграции Alembic** как единственный источник схемы (семь ревизий MVP).

**Аудитория:** разработчики и tech lead, которые оценивают или дорабатывают компактный ERP/OMS/WMS backend. В репозитории — MVP доменной логики и HTTP API; без готовой SaaS-обвязки и без general ledger.

---

## Основные возможности

Статусы: **Реализовано** | **Частично** | **Запланировано**

| Область | Статус | Примечание |
|---------|--------|------------|
| Product catalog | Реализовано | SKU через catalog API и domain service |
| Customers & price lists | Реализовано | Retail / wholesale / B2B / special |
| Suppliers & supplier products | Реализовано | Каталог поставщика; ARQ sync — счётчик чтений (hook) |
| Warehouses | Реализовано | Справочник складов |
| Inventory levels & movements | Реализовано | Receipt, reservation, release, shipment, transfer, return; журнал движений |
| Stock adjustment (`ADJUSTMENT`) | Частично | Enum и RBAC-право есть; отдельного public adjust API в routers нет |
| Order management | Реализовано | DRAFT → … → SHIPPED (state machine) |
| Pricing resolution | Реализовано | Цена при confirm заказа |
| Invoicing | Реализовано | Выпуск при `RESERVED`; expiry отменяет заказ и освобождает stock |
| Payments | Реализовано | `PaymentAttempt` + идемпотентный webhook по `external_event_id` |
| Partial line shipment | Реализовано | `ship_order_line`; защита от overship (constraints + тесты) |
| Purchasing (PO & goods receipt) | Реализовано | PO и частичные приёмки |
| Warehouse transfers | Реализовано | Domain + unit-тесты |
| Returns | Частично | Create (заказ `SHIPPED`/`COMPLETED`), accept → движение `RETURN`, cancel; без list API и refund |
| Reporting | Реализовано | Stock, sales summary, unpaid invoices |
| Audit log | Реализовано | Запись при мутирующих операциях (actor из контекста запроса) |
| Background jobs (ARQ) | Частично | Invoice expiry подключён; notifications/reconcile — заглушки |
| HTTP API (FastAPI) | Реализовано | Routers по доменам под `/api/...` |
| RBAC | Частично | Проверки на routes через `X-User-Role` (dev/demo transport; не production authentication) |
| Refunds | Запланировано | В коде нет |
| General ledger / double-entry | Запланировано | Вне scope MVP |

---

## Основные бизнес-процессы

### Продажа (реализованный путь)

Проверено по domain services и тестам (`tests/unit`, `tests/integration`):

1. **Создание** черновика заказа (warehouse, SKU, quantity).
2. **Confirm** — расчёт цен по pricing rules.
3. **Reserve** — резервы и движения `RESERVATION`; заказ → `RESERVED`.
4. **Invoice** — только при `RESERVED` → `PENDING_PAYMENT`.
5. **Оплата** — webhook: attempt, invoice и order → `PAID` (идемпотентность по event id).
6. **Assemble** — `start_assembling` → `ASSEMBLING`.
7. **Ship** — `ship_order` или `ship_order_line`.
8. **Stock** — `on_hand` / `reserved` / movements только через inventory services.

```mermaid
sequenceDiagram
    participant API
    participant Orders
    participant Pricing
    participant Inventory
    participant Invoices
    participant Payments

    API->>Orders: create draft
    API->>Orders: confirm
    Orders->>Pricing: resolve line prices
    API->>Orders: reserve
    Orders->>Inventory: reserve per line
    API->>Invoices: issue (order RESERVED)
    API->>Payments: create attempt + webhook
    Payments->>Invoices: mark paid
    Payments->>Orders: mark paid
    API->>Orders: start assembling
    API->>Orders: ship (full or partial)
    Orders->>Inventory: shipment movements
```

### Закупка (реализованный путь)

1. **Supplier** и **supplier products** (закупочные цены).
2. **Purchase order** и confirm.
3. **Goods receipt** (полная или частичная) — прирост `on_hand` через inventory receipt.
4. Остатки и движения отражают приёмку.

---

## Архитектура

**Modular monolith:** один деплой FastAPI, пакеты `src/erp_oms_wms/domains/`, тонкие HTTP routers, ARQ worker для фоновых задач.

| Domain | Ответственность |
|--------|-----------------|
| Catalog | Products / SKU |
| Customers | Клиенты, price list |
| Suppliers | Поставщики и цены закупки |
| Warehouses | Склады |
| Inventory | **Единственный writer** `on_hand`, `reserved`, movements; владеет reservations |
| Pricing | Price lists и resolution |
| Orders | Жизненный цикл заказа и отгрузки |
| Invoices | Состояние счёта |
| Payments | Payment attempts и webhooks |
| Purchasing | PO и goods receipt |
| Transfers | Межскладские перемещения |
| Returns | Обработка возвратов |
| Reporting | Агрегаты read-side |
| Audit | Append-only аудит |

**Как в коде:**

- **Inventory** меняет остатки; заказы инициируют reserve/release/ship через inventory.
- **Reservations** — подсистема inventory, не отдельная «stock-таблица» заказов.
- **PostgreSQL** — источник истины; integration-тесты: `alembic upgrade head` (без `create_all` на PG).
- **Redis** — брокер ARQ; инварианты (гонка за резерв) — транзакции и constraints БД, не Redis locks.
- **Domain services** координируют cross-domain вызовы (payments → invoices + orders).

```mermaid
flowchart LR
    subgraph clients [Clients]
        HTTP[HTTP clients]
    end
    subgraph app [Application]
        API[FastAPI routers]
        DOM[Domain services]
        API --> DOM
    end
    subgraph data [Data and async]
        PG[(PostgreSQL)]
        REDIS[(Redis)]
        ARQ[ARQ worker]
    end
    HTTP --> API
    DOM --> PG
    ARQ --> DOM
    ARQ --> REDIS
```

Подробнее: [docs/context.md](docs/context.md), [docs/01-overview/architecture.md](docs/01-overview/architecture.md), [docs/02-domain/domain-map.md](docs/02-domain/domain-map.md).

---

## Ключевые инженерные решения

| Тема | Задача | Как в репозитории |
|------|--------|-------------------|
| Transaction boundaries | Согласованность cross-domain шагов | `Session` на request/job; nested savepoints на идемпотентность webhook |
| Concurrent reservation | Два заказа на последнюю единицу | Конкуренция в БД; integration test `test_concurrent_reserve_last_unit` |
| Overselling | Отгрузить больше заказанного | Лимиты `ship_order_line` + migration `0007`; unit/integration тесты |
| Webhook idempotency | Повтор события провайдера | Уникальный `external_event_id`; PG-тесты (последовательно и параллельно) |
| State machines | Недопустимые переходы | Таблицы переходов в domain code |
| Stock atomicity | Каждое изменение qty с основанием | Журнал `StockMovement` с типами |
| Invoice expiry | Неоплаченный заказ держит резерв | `expire_due_invoices` + cancel/release (идемпотентный повтор на PG) |
| Background work | Периодическая очистка | ARQ (`erp_oms_wms.worker.WorkerSettings`); часть jobs — MVP stubs |
| RBAC | Разграничение по ролям | `require_roles` / `require_permission`; `X-User-Role` для локальной демонстрации, **не** замена JWT/OAuth/IAM |
| Audit | Кто и что изменил | `audit.record` на мутирующих API paths |

Описанные инженерные решения подтверждаются кодом и тестами. Формальная верификация и production hardening не проводились.

---

## Технологический стек

Минимальные версии — [pyproject.toml](pyproject.toml).

| Технология | Назначение |
|------------|------------|
| Python 3.13+ | Runtime |
| FastAPI ≥ 0.115 | HTTP API, OpenAPI |
| SQLAlchemy 2.x ≥ 2.0.36 | ORM, sessions |
| psycopg 3 ≥ 3.2 | Драйвер PostgreSQL (`postgresql+psycopg://`) |
| PostgreSQL 16 | Основное хранилище (`compose.yml`) |
| Alembic ≥ 1.14 | Миграции (`0001`–`0007`) |
| Redis ≥ 5.2 | Брокер ARQ |
| ARQ ≥ 0.26 | Фоновые задачи |
| Pydantic ≥ 2.9 | Валидация и схемы |
| Docker Compose | Локально: Postgres, Redis, app, worker |
| pytest ≥ 8.3 | Unit + integration |
| Ruff ≥ 0.8 | Lint и format |
| mypy ≥ 1.13 | Статическая типизация |

---

## Структура репозитория

```text
ERP-OMS-WMS/
├── alembic/                 # Alembic + scripts миграций
├── docs/                    # Публичная документация (кратко)
├── src/erp_oms_wms/
│   ├── api/                 # FastAPI, routers, RBAC, schemas
│   ├── domains/             # Бизнес-логика по bounded context
│   ├── jobs/                # Entrypoints ARQ
│   ├── db.py                # Engine и session helpers
│   ├── main.py              # Application factory
│   └── worker.py            # ARQ WorkerSettings
├── tests/
│   ├── unit/                # Быстрые тесты (SQLite in-memory)
│   └── integration/         # PostgreSQL + Alembic (pytest marker)
├── compose.yml              # app, worker, postgres:16, redis:7
├── pyproject.toml
├── Makefile                 # test, lint, typecheck
└── README.md
```

---

## Быстрый старт

### Требования

- Python **3.13+**
- [uv](https://docs.astral.sh/uv/) (рекомендуется) или pip
- Docker и Docker Compose

### Рекомендуемый путь: PostgreSQL через Compose

1. Клонировать репозиторий и установить зависимости:

   ```bash
   uv sync
   ```

2. Настроить окружение:

   ```bash
   cp .env.example .env
   ```

   **`DATABASE_URL`** — канонический вид `postgresql+psycopg://…` (драйвер **psycopg 3** в [pyproject.toml](pyproject.toml)).
   Переменную читают API (`get_engine`), Alembic (`alembic/env.py`) и ARQ worker (`jobs/*` через `session_scope`). См. [.env.example](.env.example) и [.env.postgres.example](.env.postgres.example).

3. Поднять инфраструктуру:

   ```bash
   docker compose up -d postgres redis
   ```

4. Применить миграции:

   ```bash
   uv run alembic upgrade head
   ```

5. Запустить API:

   ```bash
   uv run uvicorn erp_oms_wms.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. Документация API:

   - Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
   - Health: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

7. (Опционально) ARQ worker с теми же `DATABASE_URL` и Redis:

   ```bash
   docker compose up -d worker
   ```

   Локально: `uv run arq erp_oms_wms.worker.WorkerSettings`

### Весь стек в Docker

```bash
docker compose up --build
```

Сервис `app` слушает порт **8000**, Postgres и Redis — из того же `compose.yml`.

### SQLite и PostgreSQL

| Режим | Назначение |
|-------|------------|
| **SQLite** | Только **unit**-тесты (`tests/conftest.py`, in-memory). Не для production-путей MVP. |
| **PostgreSQL** | Реальная схема, миграции и **integration**-тесты. Рекомендуется для локальной работы с API. |

---

## Тестирование

| Набор | Команда | БД |
|-------|---------|-----|
| Unit (+ health API) | `make test` или `uv run pytest -q` | SQLite in-memory |
| Lint / types | `make lint`, `make typecheck` | — |
| Integration | `TEST_DATABASE_URL='postgresql+psycopg://user:password@localhost:5432/erp-oms-wms-test' uv run pytest tests/integration -m integration -v` | PG 16; схема через `alembic upgrade head` |

**Сбор:** 28 тестов (по умолчанию выбирается 22; 6 integration — только с `-m integration`).

**Критичные сценарии на PostgreSQL** (`tests/integration/test_postgres_critical.py`, `test_reserve_concurrency.py`):

- Повторный confirm заказа — без дублирующих резервов/движений
- Частичная отгрузка и защита от overship
- Последовательная идемпотентность payment webhook
- Идемпотентность invoice expiry (освобождение резерва)
- Параллельный дублирующий webhook
- Конкурентный резерв последней единицы

CI ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)): Ruff, mypy, pytest, `docker compose config`, `alembic upgrade head` на service Postgres.

---

## Документация

Точка входа: [docs/README.md](docs/README.md).

| Тема | Ссылки |
|------|--------|
| Обзор | [docs/context.md](docs/context.md) |
| Архитектура | [docs/01-overview/architecture.md](docs/01-overview/architecture.md) |
| Домены | [docs/02-domain/domain-map.md](docs/02-domain/domain-map.md) |
| Конкурентность | [docs/05-data-integrity/concurrency.md](docs/05-data-integrity/concurrency.md) |
| Background jobs | [docs/06-tech/background-jobs.md](docs/06-tech/background-jobs.md) |

---

## Текущие ограничения

**MVP backend** (без production hardening):

- **Нет JWT/OAuth** — аутентификация не реализована. RBAC **действует** при заданном `X-User-Role`; заголовок — для **разработки/демо**, не для production IAM.
- **Нет refund** и нет интеграции с реальным payment provider (mock webhook).
- **Stock adjustment API** — право в RBAC есть; полного adjust endpoint под `ADJUSTMENT` нет.
- **Returns (частично)** — `POST /returns`, `POST /returns/{id}/accept`, `POST /returns/{id}/cancel` для `SHIPPED`/`COMPLETED`; accept пишет `RETURN` в inventory. Нет: refunds, расширенного RMA, listing, полного набора правил из requirements.
- **Background jobs** — `send_notifications` и `reconcile_payments` — заглушки; expiry и reporting — рабочие пути.
- **Нет GL / double-entry** — финансовая правда: invoice + payment attempt.
- **Single-process deployment** — нет руководства по multi-tenant и горизонтальному масштабированию.

Для production ERP закладывайте отдельные auth (не только `X-User-Role`), ops и свой чеклист hardening.
