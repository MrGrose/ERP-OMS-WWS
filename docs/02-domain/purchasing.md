# Домен: Purchasing (Закупки)

## Статус
**PROPOSED**

## 1. Назначение и граница домена
Управление закупками у поставщиков: создание заказов поставщикам, отслеживание приемки, управление счетами от поставщиков.

## 2. Основные сущности
- **PurchaseOrder** — заказ поставщику (id, supplier_id, status, created_at)
- **PurchaseOrderLine** — позиция (po_id, sku, qty, unit_price)
- **GoodsReceipt** — приемка товара (po_id, status, qty_received)

## 3. Основные процессы
- Создание ПО → рассчет по Inventory reorder_point
- Подтверждение → отправка поставщику
- Приемка → GoodsReceipt → инициирование +on_hand в Inventory
- Счет от поставщика → Invoices domain
- Оплата → Payments domain

## 4. Граница интеграции
**Входящие:**
- **Suppliers** → supplier info, terms
- **Inventory** → reorder_point, lead_time

**Исходящие:**
- → **Inventory**: GoodsReceipt → +on_hand (RECEIPT)
- → **Invoices**: счет от поставщика
- → **Payments**: требование оплаты поставщику

## 5. Инварианты и правила
- BR-030: ПО может быть создан только для существующего поставщика
- BR-031: GoodsReceipt.qty <= PurchaseOrder.qty (не более заказанного)
- BR-032: Приемка товара всегда → +on_hand в Inventory

## 6. Состояния ПО
Детали в `docs/04-state-machines/purchase_order.md`

## 7. Журнал и аудит
- Все ПО и GoodsReceipt логируются в audit_log

## 8. Интеграция
- Inventory → reorder_point signal → создание ПО
- GoodsReceipt → Inventory RECEIPT (+on_hand)
- ПО → Invoices (счет от поставщика)

## 9. OPEN вопросы
- [ ] Автоматический ПО при reorder_point?
- [ ] Partial receipt with backorder?
- [ ] Quality inspection перед приемкой?
