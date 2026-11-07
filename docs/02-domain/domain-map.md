# Карта доменов и интеграция (Domain Map)

## Матрица доменов (12 доменов)

| Домен | Статус | Основная ответственность | Инициирует | Получает |
|-------|--------|--------------------------|-----------|----------|
| **Inventory** | CONFIRMED | Остатки, резервы, доступность | StockMovement, Reservations | Orders, Purchasing, Warehouse |
| **Reservations** | CONFIRMED | Подсистема Inventory: создание/освобождение резервов | (в Inventory) | Orders инициирует |
| **Orders** | CONFIRMED | Заказы покупателей, позиции, статусы | Reservations (инициирует), Payments, Invoices | Payments, Inventory остатки |
| **Purchasing** | PROPOSED | Закупки, заказы поставщикам, прием товара | GoodsReceipt, Invoices | Inventory, Warehouse |
| **Invoices** | PROPOSED | Счета покупателям и поставщикам | Payments, Accounting | Orders, Purchasing, Payments |
| **Payments** | CONFIRMED | Платежи (PaymentAttempt), источник истины оплаты | (инициирует за счетом) | Orders, Invoices, Accounting |
| **Customers** | PROPOSED | Клиенты, контакты, кредиты, история | Orders, Payments | Pricing, Audit |
| **Suppliers** | PROPOSED | Поставщики, контакты, условия | Purchasing, Invoices | Audit |
| **Warehouses** | PROPOSED | Склады, локации, вместимость, зоны | StockMovement, Purchasing | Inventory, Audit |
| **StockMovement** | PROPOSED | Журнал движений: RECEIPT, SHIPMENT, TRANSFER, ADJUSTMENT, RETURN, WRITE_OFF, RECOUNT | Inventory writer | Inventory reader, Audit |
| **Pricing** | OPEN | Каталог цен, скидки, тарифы | Orders, Invoices | Orders reader |
| **Audit & Reporting** | OUT_OF_SCOPE |GL, двойная запись, 1С-уровень финансовая консолидация | (читает из доменов) | – |

---

## Ключевые инварианты

### Inventory (единственный writer остатков)
- **CONFIRMED**: `available = on_hand - reserved`
- **CONFIRMED**: `on_hand` уменьшается только через `StockMovement` с типом `SHIPMENT`
- **CONFIRMED**: Резервирование **не** уменьшает `on_hand`; отгрузка — отдельная операция
- **CONFIRMED**: Любое изменение остатка = основание + запись в `StockMovement` журнал

### Reservations (подсистема Inventory)
- **CONFIRMED**: Создание/освобождение резервов только в Inventory
- **CONFIRMED**: Orders **инициирует** резервирование (вызов), но **не пишет** остатки
- **CONFIRMED**: Резерв может быть отменен, если заказ отменен

### Payments (источник истины)
- **CONFIRMED**: `PaymentAttempt` — единственная система для оплат
- **CONFIRMED**: Платеж не читается из `order.is_paid`; заказ читает статус платежа из Payments

### Междоменные сценарии
- **CONFIRMED**: По `docs/02-domain/cross-domain-flows.md`
- **CONFIRMED**: Не писать в чужие таблицы в обход сервисов

---

## 12 доменов: детальные ссылки

1. [Inventory](./inventory.md)
2. [Reservations](./inventory-reservations.md) (подсистема Inventory)
3. [Orders](./orders.md)
4. [Purchasing](./purchasing.md)
5. [Invoices](./invoices.md)
6. [Payments](./payments.md)
7. [Customers](./customers.md)
8. [Suppliers](./suppliers.md)
9. [Warehouses](./warehouses.md)
10. [StockMovement](./stock-movement-semantics.md)
11. [Pricing](./pricing.md)
12. [Audit & Reporting](./audit.md)

---

## Архитектурные решения

- **Отсутствие GL, двойной записи**: OUT_OF_SCOPE; для бухгалтерского учета используется интеграция с 1С или аналогичной системой
- **Отсутствие OPEN состояний**: Не реализовывать без явного решения в `docs/decisions/`
- **Таблица audit_log**: Все изменения сущностей записываются для трассировки и аудита
- **Event sourcing**: PROPOSED — рассмотреть для StockMovement и Orders

---

## Следующие шаги
- [ ] Уточнить Pricing domain (OPEN)
- [ ] Определить Audit & Reporting scope (может быть отдельное решение)
- [ ] Согласовать cross-domain flows в `docs/02-domain/cross-domain-flows.md`
