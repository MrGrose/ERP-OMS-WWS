# Inventory core — первая реализация

**Статус:** CONFIRMED (код в репо)  
**Дата:** 2026-11-07

## Решение

Пакет `src/erp_oms_wms/domains/inventory/`: модели `InventoryLevel`, `StockMovement`, `Reservation`; сервис `reserve_for_order`, `release_reservation`, `ship_reservation`, `apply_receipt`.

Журнал: каждое изменение through `_append_movement` (BR-004).

## Не трогали

Orders API, Payments, Alembic на проде (миграция `20261107_0001` — schema only).

## Тесты

`tests/unit/test_inventory_service.py` — SQLite in-memory, 5 сценариев + health.

## Риски

- `SELECT FOR UPDATE` на SQLite в тестах; на PostgreSQL — проверить интеграционно.
- SHIPMENT одной записью (on_hand и reserved) — OPEN в stock-movement-semantics.
