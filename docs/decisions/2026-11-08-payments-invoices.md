# Payments + Invoices

**Дата:** 2026-11-07

## Реализовано

- `Invoice` (PENDING_PAYMENT → PAID | EXPIRED)
- `PaymentAttempt` + webhook идемпотентность (`external_event_id` unique)
- Успех → `Order.mark_paid` (RESERVED → PAID)
- `expire_invoices` ARQ job → EXPIRED + `cancel_order` (release)

## Дальше

- Purchasing / PurchaseOrder / GoodsReceipt (OPEN SM)
- Реальный payment provider
