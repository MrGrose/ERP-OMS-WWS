# ERP-OMS-WWS Documentation Index

**Status**: Foundation Phase ✓ COMPLETE  
**Last Updated**: 2026-11-07

---

## Quick Links

Start here:
1. **[Vision & Goals](./01-overview/vision.md)** — What is this project?
2. **[Architecture Overview](./01-overview/architecture.md)** — How it all fits together
3. **[Domain Map](./02-domain/domain-map.md)** — 12 domains and their relationships
4. **[Open Questions](./open-questions.md)** — What's not yet decided?

---

## Documentation Structure

### 01-overview/ — Project-level
- `vision.md` — Goals, scope, roadmap, success metrics
- `architecture.md` — High-level system design, data flows, integration points

### 02-domain/ — Domain-Driven Design
- `_DOMAIN_TEMPLATE.md` — Template for new domains (9 sections)
- `domain-map.md` — Matrix of 12 domains, key invariants, integration grid
- **Individual domain specs** (each 9 sections per template):
  - `inventory.md` — Inventory management, single writer for on_hand, reserved
  - `inventory-reservations.md` — Subsystem of Inventory; reserve/release/shipment
  - `orders.md` — Customer orders, create → reserve → ship → deliver
  - `purchasing.md` — Supplier orders, PO, GoodsReceipt
  - `invoices.md` — Billing (to customers, from suppliers)
  - `payments.md` — Source of truth: PaymentAttempt (not order.is_paid)
  - `customers.md` — Customer data, credit limits, history
  - `suppliers.md` — Supplier data, terms, pricing
  - `warehouses.md` — Physical storage: locations, zones, capacity
  - `pricing.md` — Pricelist, discounts (OPEN domain)
  - `audit.md` — Audit & reporting (OUT_OF_SCOPE: GL, double-entry)
- `stock-movement-semantics.md` — 8 movement types (RECEIPT, SHIPMENT, etc) with table
- `cross-domain-flows.md` — 6 main business flows (Order→Shipment, PO→Receipt, Return, Transfer, Count, Invoice→Payment)

### 03-business-rules/
- `registry.md` — All business rules BR-001+ (at least 25 rules with test criteria, status tags)

### 04-state-machines/
- `order.md` — CONFIRMED states and transitions (DRAFT → PENDING → CONFIRMED → SHIPPED → DELIVERED)
- `invoice.md` — PROPOSED (DRAFT → ISSUED → PAID / OVERDUE / CANCELLED)
- `payment_attempt.md` — CONFIRMED (PENDING → SUCCESS / FAILED → REFUNDED)
- `reservation.md` — CONFIRMED (ACTIVE → SHIPPED / RELEASED / PARTIALLY_SHIPPED)
- `purchase_order.md` — PROPOSED (DRAFT → PENDING → RECEIVED → INVOICED → PAID)
- `goods_receipt.md` — PROPOSED (DRAFT → RECEIVED → QUALITY_PASSED → CONFIRMED)
- `return.md` — PROPOSED (INITIATED → REQUESTED → IN_TRANSIT → RECEIVED → ACCEPTED / REJECTED)
- `warehouse_transfer.md` — PROPOSED (DRAFT → PENDING → IN_TRANSIT → RECEIVED → COMPLETED)

### 05-data-integrity/
- `concurrency.md` — Race condition prevention, locking strategy, idempotency, deadlock prevention

### 06-tech/
- `stack-constraints.md` — Tech stack (Python, FastAPI, PostgreSQL, React), architectural rules
- `background-jobs.md` — Async jobs (reorder signals, reconciliation, dunning, cleanup)
- *(agent skills)* — локально: `.cursor/agent/docs/agent-skills.md` (не в Git)

### 07-testing/
- `strategy.md` — Test pyramid (70% unit, 25% integration, 5% e2e), pytest, Playwright, CI/CD

### Top-level docs/
- *(agent boundaries / checklist)* — локально: `.cursor/agent/docs/` (не в Git)
- `definition-of-ready.md` — Checklist before starting a task (clarity, design, testing plan)
- `definition-of-done.md` — Checklist before completing a task (tests, docs, BR compliance, security)
- `open-questions.md` — 21 OPEN questions with priority and blockers (multi-warehouse strategy, partial shipments, payment retry, etc)

---

## Key Files by Purpose

### "I want to understand the project"
1. Read `01-overview/vision.md` (2 min)
2. Skim `01-overview/architecture.md` (5 min)
3. Check `02-domain/domain-map.md` matrix (3 min)

### "I'm implementing a domain"
1. Read domain spec (e.g., `02-domain/inventory.md`)
2. Check state machine (e.g., `04-state-machines/order.md`)
3. Validate against BR-xxx in `03-business-rules/registry.md`
4. Check `02-domain/cross-domain-flows.md` for integrations
5. Verify with `definition-of-done.md` before merging

### "I need to know if something is in scope"
→ Check `01-overview/vision.md` (Goals, Out of Scope)  
→ Check `open-questions.md` if unclear

### "There's a bug in inventory logic"
1. Read `02-domain/inventory.md` (invariants)
2. Check `03-business-rules/registry.md` (BR-001 to BR-009)
3. Check `04-state-machines/` (if state machine involved)
4. Check `05-data-integrity/concurrency.md` (if race condition)
5. Use `/systematic-debugging` skill

### "I'm designing a new feature"
1. Use `/architect-advisor` skill
2. Check `02-domain/domain-map.md` (which domain?)
3. Check `02-domain/cross-domain-flows.md` (dependencies?)
4. Check `open-questions.md` (is this already a question?)
5. Document decision in `docs/decisions/` (if major)

---

## Status Tags Used

- **CONFIRMED** — Decided, not changing (architecture, core rules)
- **PROPOSED** — Best guess, open to refinement
- **OPEN** — Not yet decided, needs clarification / stakeholder buy-in
- **OUT_OF_SCOPE** — Explicitly excluded from this project (GL, double-entry, 1С integration)

---

## Summary by Status

| Category | CONFIRMED | PROPOSED | OPEN | OUT_OF_SCOPE |
|----------|-----------|----------|------|---|
| **Domains** | Inventory, Orders, Reservations, Payments | Purchasing, Invoices, Customers, Suppliers, Warehouses, Audit | Pricing | – |
| **Business Rules** | 20+ BR-xxx | 15+ BR-xxx | 5+ BR-xxx | – |
| **State Machines** | Order, Payment, Reservation | PO, GoodsReceipt, Return, Transfer | – | – |
| **Processes** | Reserve, Shipment, Payment | Purchasing flow | Backorder, Partial shipment | GL accounting |

---

## 12 Domains (Quick Reference)

1. **Inventory** (CONFIRMED) — on_hand, reserved, available = on_hand − reserved
2. **Reservations** (CONFIRMED subsystem of Inventory)
3. **Orders** (CONFIRMED) — customer orders, initiates reserve
4. **Payments** (CONFIRMED) — PaymentAttempt source of truth
5. **Invoices** (PROPOSED) — billing
6. **Purchasing** (PROPOSED) — supplier orders, GoodsReceipt
7. **Customers** (PROPOSED) — client data, credit
8. **Suppliers** (PROPOSED) — vendor data
9. **Warehouses** (PROPOSED) — locations, transfers
10. **StockMovement** (PROPOSED) — 8 types: RECEIPT, SHIPMENT, TRANSFER, RESERVE, RELEASE, ADJUSTMENT, WRITE_OFF, RETURN
11. **Pricing** (OPEN) — pricelist, discounts
12. **Audit & Reporting** (OUT_OF_SCOPE for GL) — append-only audit log

---

## 6 Main Flows (Cross-Domain)

1. **Order to Shipment** — Orders, Inventory, Payments, Invoices
2. **PO to GoodsReceipt** — Purchasing, Inventory, Invoices, Payments
3. **Return** — Orders, Inventory, Payments
4. **Warehouse Transfer** — Warehouses, Inventory
5. **Physical Inventory Count** — Warehouses, Inventory
6. **Invoice to Payment** — Invoices, Payments

See `02-domain/cross-domain-flows.md` for details.

---

## Next Steps

### For PM / Architect
- [ ] Review `01-overview/vision.md` for scope
- [ ] Go through `open-questions.md` and resolve HIGH-priority items
- [ ] Create `docs/decisions/` folder for design decisions
- [ ] Plan Phase 2 (MVP implementation)

### For Developers
- [ ] Read `01-overview/architecture.md`
- [ ] Understand your assigned domain(s)
- [ ] Check `definition-of-ready.md` before starting tasks
- [ ] Use agent skills: `/architect-advisor`, `/security-review`, etc.

### For QA
- [ ] Familiarize with all state machines
- [ ] Create test scenarios from `02-domain/cross-domain-flows.md`
- [ ] Use `definition-of-done.md` for acceptance criteria
- [ ] Plan E2E test coverage per `07-testing/strategy.md`

---

## File Manifest

**Total: 26 documentation files** (complete foundation)

```
docs/
├── README.md (this file)
├── 01-overview/
│   ├── vision.md
│   └── architecture.md
├── 02-domain/
│   ├── _DOMAIN_TEMPLATE.md
│   ├── domain-map.md
│   ├── inventory.md
│   ├── inventory-reservations.md
│   ├── orders.md
│   ├── purchasing.md
│   ├── invoices.md
│   ├── payments.md
│   ├── customers.md
│   ├── suppliers.md
│   ├── warehouses.md
│   ├── pricing.md
│   ├── audit.md
│   ├── stock-movement-semantics.md
│   └── cross-domain-flows.md
├── 03-business-rules/
│   └── registry.md
├── 04-state-machines/
│   ├── order.md
│   ├── invoice.md
│   ├── payment_attempt.md
│   ├── reservation.md
│   ├── purchase_order.md
│   ├── goods_receipt.md
│   ├── return.md
│   └── warehouse_transfer.md
├── 05-data-integrity/
│   └── concurrency.md
├── 06-tech/
│   ├── stack-constraints.md
│   ├── background-jobs.md
├── 07-testing/
│   └── strategy.md
├── definition-of-ready.md
├── definition-of-done.md
└── open-questions.md
```

---

## How to Update This Index

When adding new files to docs/:
1. Create the file
2. Update this README.md with the file name and brief description
3. Link to it from relevant sections
4. Tag with status (CONFIRMED / PROPOSED / OPEN / OUT_OF_SCOPE)

---

## Questions or Issues?

- **Scope questions** → `open-questions.md`
- **Unclear requirement** → `definition-of-ready.md`
- **Architecture concern** → Escalate to architect, document in `docs/decisions/`
- **Bug or missing doc** → Create GitHub issue

---

**Foundation phase goal**: Every question has an answer. Every decision is documented. Every domain has a spec. Every rule has a test criterion.

**Status**: ✓ FOUNDATION COMPLETE (as of 2026-11-07)

**Backend MVP (2026-11-07):** реализован. См. [`reports/final-readiness-audit.md`](reports/final-readiness-audit.md) и [`README.md`](../README.md).
