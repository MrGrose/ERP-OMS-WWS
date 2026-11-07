# ADR: раскладка доменов в коде (PROPOSED)

**Статус:** PROPOSED  
**Дата:** 2026-11-07

## Контекст

Project Foundation даёт плоский `src/erp_oms_wms/`. Cursor rules PF запрещают произвольное дерево `services/` без ADR.

## Решение (предложено)

Модульный монолит: пакеты по доменам внутри `src/erp_oms_wms/domains/<name>/` (service, schemas, repository) — после старта реализации.

До принятия ADR — только scaffold PF, без domain packages.

## Границы

См. [`../02-domain/domain-map.md`](../02-domain/domain-map.md), Reservations ⊆ Inventory.

## Риски

OPEN: точное именование пакетов и coordination layer.
