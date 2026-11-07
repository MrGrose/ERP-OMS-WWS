# Домен: Warehouses (Склады)

## Статус
**PROPOSED**

## 1. Назначение
Управление физическими складами: локации, зоны хранения, вместимость.

## 2. Основные сущности
- **Warehouse** — склад (id, name, address, capacity, manager_id)
- **WarehouseZone** — зона (warehouse_id, code, type: RECEIVING/STORAGE/SHIPPING, capacity)
- **Bin/Location** — ячейка (zone_id, code, capacity, reserved_for)

## 3. Основные процессы
- Управление локациями
- Планирование вместимости
- Перемещение товара между зонами
- Отслеживание заполнения

## 4. Граница интеграции
**Входящие:**
- **Inventory** → запрос доступности по складу

**Исходящие:**
- → **Inventory**: локация для резервирования и отгрузки
- → **StockMovement**: инициирование TRANSFER между складами

## 5. Инварианты и правила
- BR-080: Warehouse.capacity >= SUM(on_hand по всем SKU)
- BR-081: WarehouseZone.type определяет допустимые операции

## 6. Состояния
- ACTIVE, INACTIVE, MAINTENANCE

## 7. Журнал и аудит
- Все изменения локаций в audit_log

## 8. Интеграция
- Inventory requests warehouse_id for reservations
- StockMovement uses warehouse_id for transfers

## 9. OPEN вопросы
- [ ] Complex location management (pallet, bin-level)?
- [ ] Wave picking?
- [ ] Cycle counting?
