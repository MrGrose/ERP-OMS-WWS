# Background jobs (ARQ)

**Статус:** **IMPLEMENTED** (регистрация + функции); cron в compose **не настроен**.

**Источник:** `src/erp_oms_wms/worker.py`, `jobs/*.py`.

| Job | Назначение | Реализация | Запуск |
|-----|------------|------------|--------|
| `expire_invoices` | Просроченные счета → EXPIRED, cancel order, release reserve | **IMPLEMENTED** — `invoice_service.expire_due_invoices` | Вручную / ARQ enqueue |
| `release_expired_reservations` | То же ядро, что expire | **IMPLEMENTED** (идемпотентно с expire) | Вручную |
| `generate_reports` | Прогон reporting агрегатов, возвращает счётчик строк | **IMPLEMENTED** stub-observable | Вручную |
| `reconcile_payments` | Счётчик PENDING `PaymentAttempt` | **PARTIAL** (read-only count) | Вручную |
| `sync_supplier_prices` | Перечитывание supplier products | **PARTIAL** (no-op sync count) | Вручную |
| `send_notifications` | «Уведомления» | **STUB** — ничего не отправляет и не меняет данные | Вручную |

## Инфраструктура

- Redis: `REDIS_HOST` / `REDIS_PORT` (в compose `redis`).
- Worker: `make worker` или сервис `worker` в compose; требует `DATABASE_URL`.

## Не в worker

Reorder signal, dunning email, cron monthly reports из старой спецификации — **PLANNED** / **OUT OF SCOPE**.

## Идемпотентность

`expire_invoices` / `release_expired_reservations` безопасно повторять для уже EXPIRED (сервисная логика).

## Тесты

Прямых unit-тестов jobs **NOT VERIFIED**; логика expire покрыта косвенно через invoice unit tests.
