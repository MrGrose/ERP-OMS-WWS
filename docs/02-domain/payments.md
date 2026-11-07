# Домен: Payments (Платежи)

## Статус
**CONFIRMED**

## 1. Назначение и граница домена
Payments — источник истины для платежей. Управляет попытками оплаты, отслеживает статус, гарантирует что платеж читается из PaymentAttempt, а не из order.is_paid.

## 2. Основные сущности
- **PaymentAttempt** — попытка оплаты (id, invoice_id, amount, status, method, created_at)
- **PaymentMethod** — способ (id, type: CARD/BANK_TRANSFER/CASH, details)

## 3. Основные процессы
- Создание платежа → PaymentAttempt при Invoices.issue
- Обработка платежа → шлюз (stripe, paypal, etc.)
- Успех/неудача → статус в PaymentAttempt
- Возврат (refund) → обратный PaymentAttempt

## 4. Граница интеграции
**Входящие:**
- **Invoices** → требование платежа (invoice_id)
- **Orders** → требование оплаты заказа

**Исходящие:**
- → **Invoices**: обновление статуса (PAID)
- → **Orders**: статус оплаты для условий отгрузки

## 5. Инварианты и правила
- **BR-050**: PaymentAttempt.status — единственный источник истины для статуса платежа
- **BR-051**: order.is_paid не используется; читать из Payments domain
- **BR-052**: Возврат платежа → новый PaymentAttempt с type=REFUND

## 6. Состояния платежа
- PENDING, SUCCESS, FAILED, REFUNDED, CANCELLED

## 7. Журнал и аудит
- Все попытки логируются (включая неудачные)
- Результат шлюза (код ошибки, ID в системе шлюза) сохраняется

## 8. Интеграция
- Invoice created → PaymentAttempt created
- PaymentAttempt succeeded → Invoice.status = PAID
- PaymentAttempt failed → retry или escalation
- Refund initiated → new PaymentAttempt (REFUND)

## 9. OPEN вопросы
- [ ] Reconciliation с bank statements?
- [ ] Partial payments?
- [ ] Payment gateway integration specifics?
- [ ] PCI compliance requirements?
