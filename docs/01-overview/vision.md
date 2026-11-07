# ERP-OMS-WWS: Vision & Goals

## Статус
**CONFIRMED**

## Что это?

Mini ERP (Enterprise Resource Planning) система для управления:
- **Orders** (заказы покупателей)
- **Inventory** (остатки товаров, многосклад)
- **Warehouse** (операции на складе, перемещения)
- **Purchasing** (закупки у поставщиков)
- **Payments** (платежи и отчисления)
- **Customers & Suppliers** (клиенты и поставщики)

Интегрируется с 1С для финансового учета (GL, balance sheet).

---

## Проблема, которую решаем

Компании с 2–10 складами тратят часы на:
- ✗ Ручное управление остатками (spreadsheets)
- ✗ Потеря заказов (нет centralized system)
- ✗ Overstock / understock
- ✗ Ошибки при отгрузке
- ✗ Неясность с платежами

**Решение**: Integrated system для end-to-end order-to-cash flow.

---

## Цели

### Phase 1: Foundation (текущая)
- [ ] Определить 12 доменов
- [ ] Документировать бизнес-правила (BR-xxx)
- [ ] Спецификировать state machines
- [ ] Setup infrastructure (dev, test, CI/CD)
- **Duration**: 2–3 недели

### Phase 2: MVP Implementation
- [ ] Inventory domain (reserve, shipment, transfers)
- [ ] Orders domain (create, confirm, cancel, return)
- [ ] Payments domain (payment attempts, reconciliation)
- [ ] Basic UI (React + shadcn/ui)
- **Duration**: 4–6 недель

### Phase 3: Expansion
- [ ] Purchasing domain (PO, GoodsReceipt)
- [ ] Multi-warehouse operations
- [ ] Advanced reporting
- [ ] Customer portal
- **Duration**: 6–8 недель

### Phase 4: Integration & Optimization
- [ ] 1С integration (GL export)
- [ ] Performance optimization
- [ ] Security audit
- [ ] Production deployment
- **Duration**: 4–6 недель

---

## Key Principles

### 1. Domain-Driven Design
- Каждый домен независим, с ясной граничей
- Доменная модель — source of truth
- No cross-domain writes (только через events/API)

### 2. Data Integrity
- Все изменения остатков — в journal (stock_movement)
- PaymentAttempt — единственный источник истины для платежей
- Audit log для всех операций

### 3. Simplicity first
- Не переусложнять (KISS)
- Reuse existing patterns
- Add complexity только когда требуется

### 4. Testing-driven
- Unit tests для logic
- Integration tests для flows
- E2E tests для user scenarios

---

## Success Metrics

| Метрика | Target | Как измерять |
|---------|--------|---|
| Uptime | 99.5% | Monitoring / SLA |
| Order processing time | < 5 sec | API benchmark |
| Inventory accuracy | 99%+ | Physical count validation |
| Payment success rate | 95%+ | Payment gateway reports |
| Code coverage | 70%+ | pytest --cov |
| Page load time | < 3s | Lighthouse / WebPageTest |

---

## Out of Scope (Phase 1–2)

- ✗ GL (General Ledger), финансовые reconciliations → 1С
- ✗ Advanced warehouse automation (picking robots, etc)
- ✗ Supply chain optimization (demand forecasting)
- ✗ Customer loyalty programs
- ✗ Multi-currency support (Phase 4 maybe)
- ✗ Compliance (GDPR, ISO, etc) — базовые, but не full audit trail

---

## Tech Stack

- **Backend**: Python 3.11, FastAPI, PostgreSQL, SQLAlchemy
- **Frontend**: React, TypeScript, shadcn/ui, Tailwind
- **Testing**: pytest, Playwright
- **DevOps**: Docker, GitHub Actions, TBD (k8s or serverless)
- **Payment**: Stripe / PayPal integration

---

## Users

### Primary
- **Warehouse Manager**: Управление остатками, переводы, инвентаризация
- **Order Fulfillment**: Создание заказов, подтверждение, отгрузка, возвраты
- **Purchasing Manager**: Закупки, приемка товара
- **Finance/Accounting**: Отчеты, платежи, reconciliation

### Secondary
- **Customers**: Самообслуживание заказов (future)
- **Suppliers**: EDI integration (future)

---

## Constraints

- **Time**: 3–4 месяца до MVP
- **Budget**: Limited (no fancy ML, no 3rd-party SaaS except payment gateway)
- **Team size**: 2–4 developers (+ PM, QA)
- **Data**: ~1M+ orders/year, multi-warehouse

---

## Risks

| Риск | Impact | Mitigation |
|------|--------|-----------|
| Неясные requirements | HIGH | Frequent stakeholder sync |
| Inventory inconsistency | HIGH | Strong constraints + testing |
| Payment gateway integration fails | MEDIUM | Fallback to manual reconciliation |
| Database performance | MEDIUM | Index optimization, partitioning |
| Team context loss | MEDIUM | Comprehensive documentation |

---

## Dependencies & Integrations

- **1С**: GL export (Phase 4)
- **Payment Gateway**: Stripe or PayPal
- **Email**: For notifications (existing service)
- **Warehouse system**: Manual input initially (API later)

---

## Roadmap

```
Week 1–2:   Foundation & documentation (current)
Week 3–4:   Database schema + unit tests
Week 5–6:   API endpoints (Orders, Inventory, Payments)
Week 7–8:   Frontend MVP (React components)
Week 9–10:  Integration testing, bug fixes
Week 11–12: Performance tuning, security audit
Week 13–16: Purchasing domain, advanced features
```

---

## Contact & Escalation

- **PM**: [name] — requirements, priorities
- **Architect**: [name] — design decisions, domain boundaries
- **DevOps**: [name] — infrastructure, deployment
- **Database**: [name] — schema design, migrations

For OPEN questions → see `docs/open-questions.md`

---

## Next: Read this next

1. `docs/02-domain/domain-map.md` — Overview of 12 domains
2. `docs/03-business-rules/registry.md` — Business rules (BR-xxx)
3. `docs/04-state-machines/` — Order, Payment, Inventory state machines
4. `docs/open-questions.md` — Unresolved issues
