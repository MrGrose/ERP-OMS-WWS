# Final readiness audit — Mini ERP / OMS / WMS

**Date:** 2026-11-07  
**Итоговый статус:** `READY WITH LIMITATIONS`

## 1. Executive summary

Проект прошёл финальный аудит по ТЗ (foundation + backend MVP). Исправлены подтверждённые дефекты: идемпотентность webhook без полного `rollback`, TOCTOU при резервировании, permissions на критичных API, inactive customer, CHECK на `order_line`, worker `DATABASE_URL`, отчёт supplier balances, CI lint/types. Документация и README приведены к демо-формату.

Ограничения: integration/Alembic на PostgreSQL не прогонялись в среде аудита (нет `TEST_DATABASE_URL`); ADJUSTMENT и JWT вне scope; часть ARQ jobs — observable stubs.

## 2. Итоговая оценка готовности

| Критерий | Оценка |
|----------|--------|
| Соответствие ТЗ MVP | Да, с задокументированными gap |
| Бизнес-инварианты inventory | Да (код + CHECK) |
| Демонстрация / README | Да |
| CI (ruff, mypy, pytest unit) | Да |
| Production-hardening | Нет (намеренно) |

## 3. Проверенные домены

| Домен | Реализован | Тесты |
|-------|------------|-------|
| Catalog | Да | косвенно |
| Customers / Pricing | Да | unit |
| Suppliers / SupplierProduct | Да | purchasing |
| Warehouses | Да | transfers |
| Inventory | Да | unit + integration* |
| Orders | Да | unit + API |
| Purchasing | Да | unit |
| Invoices / Payments | Да | unit |
| Transfers / Returns | Да | unit |
| Audit / Reporting | Да | unit pricing/report |
| ARQ jobs | Да | manual / stub |

\* integration — BLOCKED без PostgreSQL в среде аудита.

## 4. Найденные проблемы (PLAN)

См. план AUD-001 … AUD-020 (сессия аудита).

## 5. Исправленные проблемы

| ID | Исправление |
|----|-------------|
| AUD-001 | `apply_webhook`: `begin_nested()` вместо `session.rollback()` |
| AUD-002 | `reserve_order`: убран двухфазный `check_available` |
| AUD-003 | `compose.yml` worker: `DATABASE_URL` + depends_on postgres |
| AUD-004 | Permissions: orders, invoices, payments, purchasing |
| AUD-005 | Ruff/mypy: StrEnum, helpers, per-file ignores, typing |
| AUD-006/007 | `CustomerInactiveError`, блок confirm |
| AUD-008 | ORM + migration `20261107_0007` CHECK на shipped qty |
| AUD-009 | `count(distinct PurchaseOrder.id)` в supplier_balances |
| AUD-010 | Docstrings для notification stub jobs |
| AUD-012 | `.env.example`, `make migrate` |
| AUD-014 | `inventory.read` на GET levels |
| AUD-019 | unit: double confirm, inactive customer |

## 6. Удалённый код

Массового удаления не было. Убран неиспользуемый import в payments.

## 7. Бизнес-инварианты

| Инвариант | Защита |
|-----------|--------|
| available = on_hand - reserved | свойство + логика сервиса |
| reserved ≤ on_hand, nonneg | CHECK в `inventory_level` |
| резерв не уменьшает on_hand | RESERVATION movement |
| quantity_shipped ≤ quantity | CHECK `0007` + сервис |
| цена при confirm | `unit_price_cents` на CONFIRMED |
| PaymentAttempt idempotency | unique `external_event_id` + nested flush |

## 8. Транзакции и конкурентность

| Сценарий | Ожидание | Тест |
|----------|----------|------|
| Параллельный reserve 1 qty | 1 ok / 1 fail | integration (BLOCKED) |
| Двойной confirm | 409 | unit PASS |
| Двойной webhook | replay | unit PASS |
| GR повторный confirm | 409 SM | unit purchasing |

`SELECT FOR UPDATE` на `inventory_level` при резерве/отгрузке/transfer.

## 9. Миграции

| Revision | Содержание |
|----------|------------|
| 0001–0005 | inventory, orders, payments, purchasing, reference |
| 0006 | customer, product_price, supplier_product, order_line prices |
| 0007 | order_line ship CHECK |

**VERIFY Alembic на чистой БД:** BLOCKED (Postgres не поднят в среде аудита). Рекомендация: `docker compose up -d postgres && make migrate`.

## 10. API и permissions

Мутации orders/invoices/payments/purchasing/inventory receipts защищены `require_permission`. Dev default Admin без заголовка — **только для локальной разработки**.

## 11. Фоновые задачи

Все 6 функций в `WorkerSettings`. Worker требует `DATABASE_URL`. Retry/cron — стандарт ARQ, не настраивался.

## 12. Результаты тестов

| Проверка | Результат | Комментарий |
|----------|-----------|-------------|
| Ruff | **PASS** | `ruff check .` |
| Ruff format | **PASS** | |
| mypy src | **PASS** | strict |
| Unit tests | **PASS** | 22 passed, 1 deselected |
| Integration | **BLOCKED** | нет `TEST_DATABASE_URL` |
| Alembic up/down | **BLOCKED** | нет PG в среде |
| Docker Compose config | **PASS** | `docker compose config -q` |
| API smoke | **BLOCKED** | не поднимали stack в аудите |
| Clean startup | **BLOCKED** | документировано в README |

## 13. Результаты запуска

Инструкции в README. Compose валиден; миграции — отдельный шаг перед демо.

## 14. Оставшиеся ограничения

- JWT/OAuth, GL, BI, frontend.
- `ADJUSTMENT` stock — enum без API.
- FK order.customer_id → customer (строка, без FK).
- Catalog: нет barcode/category из полного ТЗ.
- ARQ: `send_notifications`, `reconcile_*`, `sync_*` — stubs.
- RBAC по заголовкам, не production auth.

## 15. Итоговый статус

**`READY WITH LIMITATIONS`** — готов к портфолио-демо после локального `docker compose up`, `alembic upgrade head`, прогона integration на PostgreSQL.

## 16. Подготовка репозитория к публикации (2026-11-07)

### Перенесённые материалы (каталог `.cursor/agent/`)

| Источник | Назначение |
|----------|------------|
| `AGENTS.md` (полный) | `.cursor/agent/AGENTS.md` |
| `FOUNDATION_MANIFEST.md` | `.cursor/agent/` |
| `pf-answers.json` | `.cursor/agent/` |
| `.cursor/README.md` | `.cursor/agent/README.md` |
| `.cursor/plans/` | `.cursor/agent/plans/` |
| `.agents/skills/` | `.cursor/agent/skills/` (+ симлинк `.agents/skills`) |
| `docs/agent-checklist.md` | `.cursor/agent/docs/` |
| `docs/agent-boundaries.md` | `.cursor/agent/docs/` |
| `docs/06-tech/agent-skills.md` | `.cursor/agent/docs/agent-skills.md` |
| рабочие копии ТЗ/плана | `.cursor/agent/reference/` |

**На месте (локально, не в Git):** `.cursor/rules/`, `.cursor/commands/` — требуются Cursor.

**Очистка репозитория (2026-11-07):** план foundation и foundation-audit перенесены в `.cursor/agent/reference/` (локально, не в Git). Канон ТЗ — только `docs/requirements/ERP-OMS-WMS.md`. Корневой дубликат ТЗ и пустой `docs/04-deployment/docker.md` удалены; Docker описан в `README.md` и `docs/02-development/local-setup.md`.

### `.gitignore`

```
.cursor/agent/
.cursor/rules/
.cursor/commands/
.agents/
```

Широких масок нет (устранена ошибочная запись `.*`).

### Остаётся в Git (публично)

- `AGENTS.md` — краткий указатель для контрибьюторов
- `README.md`, `docs/**` (домены, BR, отчёты, `requirements/ERP-OMS-WMS.md`)
- `.foundation.json` (manifest PF; план/аудит foundation — в локальном `.cursor/agent/reference/`)
- `src/`, тесты, Alembic, CI, Docker

### Проверка Git index

- `git ls-files` (174 файла) — **нет** `.cursor/agent`, `.cursor/rules`, `.cursor/commands`, `.agents`, `SKILL.md`
- `git check-ignore` — agent/rules/commands/agents подтверждены
- `git rm --cached` для agent paths **не потребовался**
- Commit / push **не выполнялись**

### Работоспособность Cursor

| Механизм | Путь |
|----------|------|
| Rules | `.cursor/rules/*.mdc` (13 файлов) |
| Commands | `.cursor/commands/` |
| Skills | `.cursor/agent/skills/` + `.agents/skills` → symlink |
| Политика агента | `.cursor/agent/AGENTS.md` |

### Ограничения

- На чистом clone нет rules/skills — нужна локальная копия или повторный PF scaffold.
- Корневой `AGENTS.md` в Git не содержит полной agent policy.
