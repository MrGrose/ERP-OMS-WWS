# Домен: Invoices (Счета)

## Статус
**PROPOSED**

## 1. Назначение
Управление счетами к получению (от заказов) и счетами к оплате (от поставщиков). Invoices — промежуточный артефакт между Orders/Purchasing и Payments.

## 2. Основные сущности
- **Invoice** — счет (id, type: OUTBOUND/INBOUND, customer_id/supplier_id, status, total, created_at)
- **InvoiceLine** — позиция счета (invoice_id, sku, qty, unit_price, amount)

## 3. Основные процессы
- Создание счета → Orders.confirm или GoodsReceipt
- Отправка → Customers или Suppliers
- Оплата → связь с PaymentAttempt
- Корректировка (кредит-нота) → при возврате

## 4. Граница интеграции
**Входящие:**
- **Orders** → создание счета при подтверждении
- **Purchasing** → GoodsReceipt → счет от поставщика

**Исходящие:**
- → **Payments**: требование оплаты (PaymentAttempt.invoice_id)
- → **Customers/Suppliers**: отправка документа

## 5. Инварианты и правила
- BR-040: Invoice.total = SUM(InvoiceLine.amount)
- BR-041: Счет может быть оплачен (PaymentAttempt) только если статус не CANCELLED

## 6. Состояния счета
- DRAFT, ISSUED, PAID, PARTIALLY_PAID, OVERDUE, CANCELLED

## 7. Журнал и аудит
- Все изменения статуса в audit_log
- Связь с PaymentAttempt для трассировки оплат

## 8. Интеграция
- Order confirm → Invoice creation
- GoodsReceipt confirm → Invoice from supplier
- Invoice + Payment match → Payments domain

## 9. OPEN вопросы
- [ ] Auto-invoice generation?
- [ ] Credit notes handling?
- [ ] Multi-currency support?
