# Open Questions (OPEN вопросы)

## Статус
**LIVING DOCUMENT** — обновляется по мере появления неясностей

## Назначение
Каталог всех нерешенных вопросов, которые блокируют имплементацию или требуют уточнения.

---

## Inventory & Stock Management

### Q1: Multi-warehouse allocation strategy (HIGH)
**Вопрос**: Когда Order требует товар, как выбирать между несколькими складами?
- Option A: First available (простое, но может быть inefficient)
- Option B: Optimize by distance / cost
- Option C: Manual allocation (warehouse manager decides)

**Блокирует**: Order creation logic  
**Статус**: PROPOSED (Option A для foundation)  
**Решение принято**: Когда?

---

### Q2: Reorder point automation (MEDIUM)
**Вопрос**: Автоматические ПО когда on_hand < reorder_point?
- Option A: Automatic (система создает ПО)
- Option B: Signal only (система уведомляет, человек создает)
- Option C: Not in scope (manual ordering)

**Блокирует**: Purchasing domain  
**Статус**: PROPOSED  
**Решение принято**: Когда?

---

### Q3: Stock valuation method (MEDIUM)
**Вопрос**: Как считать стоимость остатков для отчетности?
- Option A: FIFO (First In First Out)
- Option B: LIFO (Last In First Out)
- Option C: Weighted Average
- Option D: OUT_OF_SCOPE (интеграция с 1С)

**Блокирует**: Financial reporting  
**Статус**: PROPOSED (Option D вероятнее)  
**Решение принято**: Когда?

---

### Q4: Lot/Serial number tracking (MEDIUM)
**Вопрос**: Нужно ли отслеживать товар по партиям или серийным номерам?
- Option A: Yes (для лекарств, электроники, etc)
- Option B: No (только SKU level)
- Option C: Optional (feature flag)

**Блокирует**: InventoryLevel schema  
**Статус**: OPEN  
**Решение принято**: Когда?

---

### Q5: Write-off approval process (MEDIUM)
**Вопрос**: Кто может списывать товар и какой процесс?
- Option A: Warehouse manager alone
- Option B: Requires 2-person approval
- Option C: No process (free form)

**Блокирует**: WRITE_OFF state machine  
**Статус**: OPEN  
**Решение принято**: Когда?

---

## Orders & Fulfillment

### Q6: Partial shipment support (MEDIUM)
**Вопрос**: Разрешить ли отправку части заказа?
- Option A: Yes (with partial invoice)
- Option B: No (all or nothing)
- Option C: Yes but manual only

**Блокирует**: Order state machine, Shipment logic  
**Статус**: PROPOSED (Option A вероятнее)  
**Решение принято**: Когда?

---

### Q7: Backorder handling (MEDIUM)
**Вопрос**: Если stock недоступен, создать backorder или отклонить?
- Option A: Backorder (ждать товар)
- Option B: Reject (customer попробует позже)
- Option C: Manual decision

**Блокирует**: Order creation workflow  
**Статус**: PROPOSED  
**Решение принято**: Когда?

---

### Q8: Return window policy (LOW)
**Вопрос**: Как долго customer может вернуть товар?
- Option A: Fixed (e.g., 30 days)
- Option B: Per product (some 14 days, some 60 days)
- Option C: Customer-specific (VIP 90 days)

**Блокирует**: Return state machine  
**Статус**: PROPOSED (Option A для foundation)  
**Решение принято**: Когда?

---

### Q9: Restocking fee (LOW)
**Вопрос**: Есть ли комиссия за возврат?
- Option A: Yes, fixed % (e.g., 15%)
- Option B: Yes, per product
- Option C: No

**Блокирует**: Refund logic  
**Статус**: OPEN  
**Решение принято**: Когда?

---

## Payments

### Q10: Multi-part payment (MEDIUM)
**Вопрос**: Разрешить ли оплачивать Invoice несколькими платежами?
- Option A: Yes (track partial payments)
- Option B: No (one payment per invoice)
- Option C: Yes but manual only

**Блокирует**: Payment state machine  
**Статус**: PROPOSED (Option A для future)  
**Решение принято**: Когда?

---

### Q11: Payment retry strategy (HIGH)
**Вопрос**: Как обрабатывать failed платежи?
- Option A: Auto-retry (exponential backoff, 3x)
- Option B: Manual retry (customer initiates)
- Option C: Escalation (support team involved)

**Блокирует**: PaymentAttempt service  
**Статус**: PROPOSED (Option A)  
**Решение принято**: Когда?

---

### Q12: Payment gateway selection (HIGH)
**Вопрос**: Какой payment gateway использовать?
- Option A: Stripe
- Option B: PayPal
- Option C: Both
- Option D: Not decided

**Блокирует**: Payments service implementation  
**Статус**: PROPOSED  
**Решение принято**: Когда?

---

## Customers & Suppliers

### Q13: Credit limit enforcement (MEDIUM)
**Вопрос**: Как трактовать credit_limit?
- Option A: Hard limit (reject если exceeded)
- Option B: Soft limit (warn но разрешить)
- Option C: Override by admin

**Блокирует**: Order creation validation  
**Статус**: PROPOSED (Option A)  
**Решение принято**: Когда?

---

### Q14: Dunning process (LOW)
**Вопрос**: Процесс для overdue invoices?
- Option A: Automated emails (1st, 7th, 14th day)
- Option B: Manual escalation
- Option C: Out of scope

**Блокирует**: Invoice lifecycle  
**Статус**: PROPOSED (Option C для foundation)  
**Решение принято**: Когда?

---

## Audit & Compliance

### Q15: Data retention policy (MEDIUM)
**Вопрос**: Как долго хранить исторические данные?
- Option A: 7 years (tax requirement)
- Option B: 3 years
- Option C: Indefinite

**Блокирует**: Archive strategy  
**Статус**: OPEN (зависит от юрисдикции)  
**Решение принято**: Когда?

---

### Q16: PCI compliance (HIGH)
**Вопрос**: Как хранить payment card details?
- Option A: Not at all (tokenize only)
- Option B: PCI-DSS compliant storage
- Option C: Third-party processor (Stripe vaults)

**Блокирует**: Payment data schema  
**Статус**: PROPOSED (Option C)  
**Решение принято**: Когда?

---

## Reporting & Analytics

### Q17: Financial reporting scope (HIGH)
**Вопрос**: Что входит в scope ERP vs 1С?
- Option A: All accounting (GL, balance sheet)
- Option B: Only operational reports (sales, inventory)
- Option C: Export data для 1С, 1С делает accounts

**Блокирует**: Audit domain definition  
**Статус**: CONFIRMED (Option C)  
**Решение принято**: YES ✓

---

### Q18: Real-time vs batch reporting (MEDIUM)
**Вопрос**: Отчеты real-time или batch (ночной)?
- Option A: Real-time (live dashboard)
- Option B: Batch (ночной job)
- Option C: Configurable

**Блокирует**: Reporting infrastructure  
**Статус**: PROPOSED  
**Решение принято**: Когда?

---

## Infrastructure & Deployment

### Q19: Multi-warehouse deployment (MEDIUM)
**Вопрос**: Один ERP для всех складов или отдельные инстансы?
- Option A: One central ERP (multi-tenant)
- Option B: Separate instances per warehouse
- Option C: Hybrid

**Блокирует**: Warehouse domain schema  
**Статус**: PROPOSED (Option A)  
**Решение принято**: Когда?

---

### Q20: Event queue for async (MEDIUM)
**Вопрос**: Использовать ли message queue (Kafka, RabbitMQ)?
- Option A: Yes (async events, scalable)
- Option B: No (sync API calls)
- Option C: Future (start sync, migrate later)

**Блокирует**: Event-driven architecture  
**Статус**: PROPOSED (Option C)  
**Решение принято**: Когда?

---

## Process Questions

### Q21: How to resolve OPEN questions? (META)
**Вопрос**: Процесс для принятия решения по OPEN вопросам?
- Who decides? (PM, architect, domain expert?)
- Как документировать решение?
- Кто обновляет docs?

**Статус**: NEEDS_PROCESS_DEFINITION  
**Решение принято**: Когда?

---

## Summary

| Категория | # OPEN | Блокирует | Приоритет |
|-----------|--------|-----------|----------|
| Inventory | 5 | Foundation | HIGH + MEDIUM |
| Orders | 5 | Foundation | MEDIUM |
| Payments | 3 | Foundation | HIGH |
| Customers | 2 | Nice-to-have | MEDIUM |
| Audit | 2 | Foundation | MEDIUM + HIGH |
| Reporting | 2 | Phase 2 | MEDIUM |
| Infrastructure | 2 | Phase 2 | MEDIUM |
| **Total** | **21** | | |

---

## Next Steps

1. Собрать stakeholders (PM, architects, domain experts)
2. Пройти по HIGH-приоритет OPEN вопросам
3. Записать решения в `docs/decisions/`
4. Обновить affected documents
5. Replan foundation если нужно

---

## How to add new OPEN question

Template:
```
### Qx: [Title] ([PRIORITY])
**Вопрос**: [Describe ambiguity clearly]
- Option A: [alternative 1]
- Option B: [alternative 2]
- Option C: [alternative 3]

**Блокирует**: [What feature depends on this?]
**Статус**: [OPEN / PROPOSED / DECISION_NEEDED]
**Решение принято**: Когда?
```

---

**Last updated**: [date]  
**Next review**: [planned date for batch resolution]
