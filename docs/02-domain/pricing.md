# Домен: Pricing (Прайс-лист и скидки)

## Статус
**OPEN**

## 1. Назначение
Управление прайс-листами, скидками, тарифными планами. Pricing может быть включена в Customers или отдельным доменом.

## 2. Основные сущности
- **Pricelist** — прайс-лист (id, name, valid_from, valid_to)
- **PricelistItem** — позиция (pricelist_id, sku, price)
- **Discount** — скидка (id, type: FIXED/PERCENT, customer_id/order_id, amount, valid_from)

## 3. Основные процессы
- Создание прайс-листа
- Применение скидок при заказе
- Управление периодичностью (сезонные цены)

## 4. Граница интеграции
**Входящие:**
- **Orders** → request price for SKU

**Исходящие:**
- → **Orders**: price для OrderLine

## 5. Инварианты и правила
- BR-090: Pricelist.price >= 0 (или может быть negative для возвратов?)
- BR-091: Discount не может быть больше чем original price

## 6. Состояния
- ACTIVE, INACTIVE, ARCHIVED

## 7. Журнал и аудит
- История цен для аналитики

## 8. Интеграция
- Orders reads prices from Pricelist
- Discounts applied at OrderLine level

## 9. OPEN вопросы
- [ ] Separate domain или часть Customers?
- [ ] Dynamic pricing?
- [ ] Currency support?
- [ ] A/B testing for prices?
