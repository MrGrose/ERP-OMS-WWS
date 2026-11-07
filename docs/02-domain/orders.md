# Домен: Orders (Заказы)

## Статус
**CONFIRMED**

## 1. Назначение и граница домена
Управление заказами покупателей: создание, резервирование товара, подтверждение, отгрузка, отмена. Orders **инициирует** резервирование в Inventory, но **не пишет** остатки напрямую.

## 2. Основные сущности
- **Order** — заказ покупателя (id, customer_id, status, created_at, updated_at)
- **OrderLine** — позиция заказа (order_id, sku, qty, price, discount)
- **Shipment** — отгрузка (order_id, status, tracking, shipped_at)

## 3. Основные процессы
- Создание заказа → валидация доступности
- Подтверждение → инициирование резервирования в Inventory
- Подготовка отгрузки → координация с Warehouse
- Отправка → уменьшение on_hand в Inventory
- Отмена → освобождение резервов в Inventory
- Возврат товара → увеличение on_hand в Inventory

## 4. Граница интеграции
**Входящие:**
- **Customers** → customer_id, credit limit
- **Inventory** → доступность товара (available >= qty)
- **Payments** → статус платежа

**Исходящие:**
- → **Reservations**: создать резерв (RESERVE)
- → **Inventory**: инициировать отгрузку (−on_hand)
- → **Invoices**: создать счет
- → **Payments**: требование оплаты

## 5. Инварианты и правила
- BR-020: OrderLine.qty <= available (при создании)
- BR-021: Заказ может быть отменен только если status в [DRAFT, PENDING]
- BR-022: Отгрузка только если stock reserved и заказ подтвержден
- BR-023: Возврат товара увеличивает on_hand

## 6. Состояния заказа
Детали в `docs/04-state-machines/order.md`

## 7. Журнал и аудит
- Все статусы, изменения позиций записываются в audit_log
- Ссылка на stock_movement для трассировки

## 8. Интеграция
- Order → Reservation: инициирование резервов в Inventory
- Order → Shipment → Inventory: −on_hand (SHIPMENT в stock_movement)
- Order → Return → Inventory: +on_hand (RETURN в stock_movement)
- Order → Invoice: при подтверждении
- Order → Payment: требование оплаты

## 9. OPEN вопросы
- [ ] Partial shipment logic: нужна ли поддержка?
- [ ] Backorder handling: если товар недоступен, создавать backorder?
- [ ] Subscription orders: поддержка повторяющихся заказов?
