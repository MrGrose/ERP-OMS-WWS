# Mini ERP / OMS / WMS (Backend MVP)

Компактный **FastAPI + PostgreSQL** backend для каталога, складов, заказов, закупок, счетов, платежей и аудита. Проект демонстрирует предметную модель ERP/OMS/WMS: резервирование, журнал движений, транзакции, идемпотентность платежей и фоновые задачи **ARQ**.

Полное ТЗ: [`docs/requirements/ERP-OMS-WMS.md`](docs/requirements/ERP-OMS-WMS.md). Доменная документация: [`docs/context.md`](docs/context.md).

## Что решает MVP

- **Каталог и цены** — прайс-листы RETAIL / WHOLESALE / B2B / SPECIAL, фиксация цены в строке заказа при `confirm`.
- **Inventory** — `on_hand`, `reserved`, `available = on_hand - reserved`; только Inventory пишет остатки (журнал `StockMovement`).
- **Orders** — lifecycle от DRAFT до COMPLETED, частичная отгрузка.
- **Purchasing** — PO → Goods Receipt → RECEIPT в inventory.
- **Invoices / Payments** — счёт, webhook с идемпотентностью, связка с заказом PAID.
- **Transfers / Returns** — атомарные TRANSFER, RETURN на склад.
- **Reporting** — агрегирующие SQL-отчёты (не BI).
- **Audit** — запись важных действий.
- **RBAC** — роли и permissions через заголовки (без JWT).

## OUT OF SCOPE

JWT/OAuth, General Ledger / 1С, полноценный BI, frontend, полный refund/return SM, тип движения **ADJUSTMENT** (есть в enum, API не реализован), Celery.

## Стек

| Слой | Технология |
|------|------------|
| API | FastAPI, Pydantic, OpenAPI (`/docs`) |
| ORM | SQLAlchemy 2.x |
| DB | PostgreSQL 16 |
| Migrations | Alembic (`0001` … `0007`) |
| Jobs | Redis + ARQ |
| Tests | pytest (+ integration на PostgreSQL) |
| Lint / types | Ruff, mypy (strict) |
| Deploy local | Docker Compose |

## Архитектура (домены)

```mermaid
flowchart LR
  subgraph api [HTTP API]
    R[routers]
  end
  subgraph domains [domains]
    C[Catalog Customers Pricing]
    I[Inventory]
    O[Orders]
    P[Purchasing]
    IV[Invoices Payments]
    T[Transfers Returns]
    A[Audit Reporting]
  end
  DB[(PostgreSQL)]
  R --> domains
  domains --> DB
  Jobs[ARQ worker] --> domains
  Jobs --> Redis[(Redis)]
```

Код: `src/erp_oms_wms/domains/<domain>/` (models, service, enums, errors). HTTP: `src/erp_oms_wms/api/routers/`.

## Inventory и резервирование

```mermaid
sequenceDiagram
  participant O as Orders
  participant I as Inventory
  participant DB as PostgreSQL
  O->>I: reserve_for_order FOR UPDATE
  I->>DB: RESERVATION reserved +=
  Note over I,DB: on_hand не меняется
  O->>I: ship_reservation_quantity
  I->>DB: SHIPMENT on_hand -= reserved -=
```

Инварианты (и CHECK в БД): `on_hand >= 0`, `reserved >= 0`, `reserved <= on_hand`.

## Жизненный цикл заказа

```mermaid
stateDiagram-v2
  [*] --> DRAFT
  DRAFT --> CONFIRMED: confirm + цены
  CONFIRMED --> RESERVED: reserve
  RESERVED --> PAID: payment webhook
  RESERVED --> PAID: assemble path optional
  RESERVED --> CANCELLED: cancel / expired invoice
  PAID --> ASSEMBLING
  RESERVED --> ASSEMBLING
  ASSEMBLING --> SHIPPED: ship
  SHIPPED --> COMPLETED: complete
```

## Оплата и истечение счёта

```mermaid
sequenceDiagram
  participant API
  participant Pay as Payments
  participant Inv as Invoices
  participant Ord as Orders
  API->>Inv: issue PENDING_PAYMENT
  API->>Pay: webhook external_event_id
  Pay->>Pay: begin_nested flush idempotency
  Pay->>Inv: PAID
  Pay->>Ord: PAID
  Note over Inv,Ord: expire_invoices job снимает резерв через cancel
```

## Фоновые задачи (ARQ)

Зарегистрированы: `expire_invoices`, `release_expired_reservations`, `generate_reports`, `reconcile_payments`, `sync_supplier_prices`, `send_notifications`.

| Job | Назначение |
|-----|------------|
| `expire_invoices` | Просроченные счета → EXPIRED + cancel RESERVED |
| `release_expired_reservations` | То же (идемпотентно, для ТЗ) |
| `generate_reports` | Прогон агрегатов (observable count) |
| `reconcile_payments` | Счётчик PENDING PaymentAttempt |
| `sync_supplier_prices` | Перечитывание supplier products (stub sync) |
| `send_notifications` | MVP-заглушка (без реальной отправки) |

Расписание cron в compose **не** настроено — задачи ставятся вручную или внешним scheduler.

## Permissions (заголовки)

- `X-User-Role`: `Admin` | `Manager` | `WarehouseOperator` | `Accountant` (по умолчанию без заголовка = Admin, только для dev).
- `X-User-Id`: actor для audit.

Матрица: `catalog.*`, `inventory.read` / `inventory.adjust`, `orders.manage`, `payments.read`, `finance.read` — см. `src/erp_oms_wms/api/rbac.py`.

## Структура репозитория

```text
src/erp_oms_wms/     # приложение
alembic/versions/    # миграции
tests/               # unit + integration
docs/                # ТЗ, домены, BR, отчёты
compose.yml          # app + postgres + redis + worker
```

## Локальный запуск

Краткий путь (API на хосте, БД и Redis в Compose):

```bash
uv sync && cp .env.example .env
docker compose up -d postgres redis
export DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/erp-oms-wms
make migrate && make dev   # http://127.0.0.1:8000/docs
```

Worker, полный стек в контейнерах, PostgreSQL без Compose, pre-commit и pytest — [`docs/02-development/local-setup.md`](docs/02-development/local-setup.md).


## Тестирование

```bash
uv run pytest                    # unit (без integration по умолчанию)
export TEST_DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/erp-oms-wms-test
uv run pytest -m integration     # гонка резервирования (PostgreSQL)
make lint
```

## Demo-сценарий (curl)

```bash
# Прайс + приёмка
curl -X PUT localhost:8000/api/pricing/prices -H 'Content-Type: application/json' \
  -d '{"price_list":"RETAIL","sku":"DEMO-SKU","amount_cents":19900}'
curl -X POST localhost:8000/api/inventory/receipts -H 'Content-Type: application/json' \
  -d '{"warehouse_id":"wh-1","sku":"DEMO-SKU","quantity":10,"reference_id":"demo-gr"}'

# Заказ: create → confirm → reserve → invoice → pay
# (см. OpenAPI /docs для полного пути)
```

## Отчёт готовности

Финальный аудит: [`docs/reports/final-readiness-audit.md`](docs/reports/final-readiness-audit.md).
