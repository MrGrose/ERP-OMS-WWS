# Orders + API — фаза 2

**Дата:** 2026-11-07

## Сделано

- Домен `orders`: SM по ТЗ (DRAFT → … → SHIPPED/CANCELLED), резерв через `inventory.service`
- REST `/api/orders/*`, `/api/inventory/*`
- Alembic `0002_orders`
- Unit + API tests; integration concurrency — `-m integration` + PostgreSQL

## Не сделано

Payments, Invoices, PAID transition
