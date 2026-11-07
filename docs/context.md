# Context — Mini ERP / OMS / WMS Backend

## Purpose

**CONFIRMED.** Компактный backend для каталога, складов, заказов, закупок, счетов, платежей и аудита. Демонстрация согласованной предметной модели и инженерии (PostgreSQL, транзакции, конкуренция). Не полноценная 1С.

## Users

**CONFIRMED:** Admin, Manager, WarehouseOperator, Accountant (роли из ТЗ).

## Stack

FastAPI, PostgreSQL, SQLAlchemy 2.x, Alembic, Redis, ARQ, Pydantic, Docker Compose, pytest, GitHub Actions. См. [`06-tech/stack-constraints.md`](06-tech/stack-constraints.md).

## Scope

| Входит | Не входит |
|--------|-----------|
| OMS/WMS/закупки/инвентарь/платежи/аудит | GL, двойная запись, 1С (**OUT_OF_SCOPE**) |
| REST API, jobs, отчёты backend | Frontend/admin UI на этапе foundation (**OUT_OF_SCOPE**) |

## Requirements source

**CONFIRMED:** [`requirements/ERP-OMS-WMS.md`](requirements/ERP-OMS-WMS.md) — единственный канон ТЗ.

## Hub — документация

| Раздел | Файл |
|--------|------|
| Vision / architecture | [`01-overview/vision.md`](01-overview/vision.md), [`01-overview/architecture.md`](01-overview/architecture.md) |
| Domain map | [`02-domain/domain-map.md`](02-domain/domain-map.md) |
| Домены (шаблон A) | [`02-domain/_DOMAIN_TEMPLATE.md`](02-domain/_DOMAIN_TEMPLATE.md), `02-domain/*.md` |
| Reservations | [`02-domain/inventory-reservations.md`](02-domain/inventory-reservations.md) |
| Междоменные потоки | [`02-domain/cross-domain-flows.md`](02-domain/cross-domain-flows.md) |
| Stock movements | [`02-domain/stock-movement-semantics.md`](02-domain/stock-movement-semantics.md) |
| Бизнес-правила | [`03-business-rules/registry.md`](03-business-rules/registry.md) |
| State machines | [`04-state-machines/`](04-state-machines/) |
| Concurrency | [`05-data-integrity/concurrency.md`](05-data-integrity/concurrency.md) |
| Tech / jobs | [`06-tech/`](06-tech/) |
| Testing | [`07-testing/strategy.md`](07-testing/strategy.md) |
| Локальная разработка | [`02-development/local-setup.md`](02-development/local-setup.md) |
| DoR / DoD | [`definition-of-ready.md`](definition-of-ready.md), [`definition-of-done.md`](definition-of-done.md) |
| OPEN | [`open-questions.md`](open-questions.md) |
| Final readiness | [`reports/final-readiness-audit.md`](reports/final-readiness-audit.md) |

## Glossary (кратко)

- **on_hand** — физический остаток. **reserved** — резерв. **available** = on_hand − reserved (**CONFIRMED**).
- **StockMovement** — журнал изменений остатков (**CONFIRMED**).
- **PaymentAttempt** — источник истины оплаты (**CONFIRMED**).

## Invariants (кратко)

См. **BR-001…** в [`03-business-rules/registry.md`](03-business-rules/registry.md). Inventory — единственный writer остатков. Резерв не уменьшает on_hand.

## External systems

**OPEN** (провайдеры платежей, внешние SKU) — см. [`open-questions.md`](open-questions.md).
