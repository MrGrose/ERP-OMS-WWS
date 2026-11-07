# Context — ERP-OMS-WMS

**Статус:** Backend MVP (as-built), PostgreSQL, Alembic `0001`–`0007`.

## Назначение

Один сервис: каталог, склады, остатки и резервы, заказы, закупки, счета, платежи, трансферы, возвраты (частично), отчёты, audit. Демонстрация согласованной доменной модели: транзакции, конкурентный резерв, идемпотентность webhook.

## Доступ (MVP)

Роли через заголовки `X-User-Role` / `X-User-Id`. JWT/OAuth нет.

## Домены (кратко)

| Домен | Роль |
|--------|------|
| inventory | Единственный writer `on_hand` / `reserved` / movements |
| orders | Lifecycle заказа, инициирует reserve/ship |
| invoices / payments | Счёт, `PaymentAttempt`, webhook |
| purchasing | PO → goods receipt → RECEIPT |
| pricing / customers | Price lists, цена при confirm |
| … | См. [`02-domain/domain-map.md`](02-domain/domain-map.md) |

## Инварианты

- `available = on_hand - reserved` (сервис + CHECK в БД).
- Резерв не уменьшает `on_hand`; отгрузка — `SHIPMENT`.
- Оплата: источник истины — `PaymentAttempt`.

## Ограничения MVP

- Нет UI, refund, GL, production IAM.
- `ADJUSTMENT` в enum; публичного adjust API нет.
- Часть ARQ jobs — stub (`send_notifications`, `reconcile_payments`).
- Integration-тесты на PG: локально (`-m integration`), не в `ci.yml`.

## Публичная навигация

| Тема | Файл |
|------|------|
| Индекс | [`README.md`](README.md) |
| Архитектура | [`01-overview/architecture.md`](01-overview/architecture.md) |
| Карта доменов | [`02-domain/domain-map.md`](02-domain/domain-map.md) |
| Конкурентность | [`05-data-integrity/concurrency.md`](05-data-integrity/concurrency.md) |
| Jobs | [`06-tech/background-jobs.md`](06-tech/background-jobs.md) |
