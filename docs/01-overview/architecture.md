# ERP Architecture Overview

## Статус
**CONFIRMED**

## Назначение
Высокоуровневая архитектура системы: слои, доменов, data flow, integration points.

---

## System Context

```
┌─────────────────────────────────────────────────────────┐
│                  ERP-OMS-WWS System                      │
│  (Orders, Warehouse, Inventory Management)               │
└─────────────────────────────────────────────────────────┘
         ↓ Export                ↑ GL Import
┌─────────────────────────────────────────────────────────┐
│                      1С (Accounting)                     │
│  (General Ledger, Balance Sheet, Tax Reporting)          │
└─────────────────────────────────────────────────────────┘

        ↓ Webhook / API
┌─────────────────────────────────────────────────────────┐
│           Payment Gateway (Stripe / PayPal)              │
└─────────────────────────────────────────────────────────┘

        ← Customer / Supplier integration (future)
```

---

## Layered Architecture

```
┌───────────────────────────────────────────────────────┐
│          Frontend Layer                                │
│  (React, shadcn/ui, Tailwind)                          │
│  - Order Management UI                                 │
│  - Inventory Dashboard                                 │
│  - Warehouse Operations                                │
│  - Finance Reports                                     │
└───────────────────────────────────────────────────────┘
                    ↓ HTTP / REST
┌───────────────────────────────────────────────────────┐
│          API Layer (FastAPI)                           │
│  - /orders, /inventory, /payments, etc                 │
│  - Request validation, Auth (JWT)                      │
│  - Response serialization                              │
└───────────────────────────────────────────────────────┘
                    ↓ Service layer calls
┌───────────────────────────────────────────────────────┐
│        Domain Services (Business Logic)                │
│  src/<domain>/                                         │
│  - orders.service.py (order creation, state machine)  │
│  - inventory.service.py (reserve, shipment, balance)  │
│  - payments.service.py (PaymentAttempt handling)      │
│  - warehouse.service.py (transfers, rebalancing)      │
│  ... (other domain services)                           │
└───────────────────────────────────────────────────────┘
                    ↓ ORM calls
┌───────────────────────────────────────────────────────┐
│        Data Access Layer (SQLAlchemy ORM)              │
│  - Models: Order, InventoryLevel, PaymentAttempt, ... │
│  - Queries: optimized with indexes                     │
│  - Transactions: SERIALIZABLE for inventory ops       │
└───────────────────────────────────────────────────────┘
                    ↓ SQL
┌───────────────────────────────────────────────────────┐
│        Database Layer (PostgreSQL)                     │
│  - Tables: orders, inventory_level, stock_movement,   │
│    payment_attempt, invoice, audit_log, ...           │
│  - Constraints: CHECK, UNIQUE, FK                      │
│  - Triggers: append-only audit_log, stock_movement    │
└───────────────────────────────────────────────────────┘
```

---

## Domain Architecture (12 domains)

```
                    ┌─────────────────┐
                    │  Customers      │
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          ↓                  ↓                  ↓
    ┌──────────┐      ┌──────────┐      ┌──────────┐
    │  Orders  │      │ Pricing  │      │  Audit   │
    └──┬───────┘      └──────────┘      └──────────┘
       │
       │ inits RESERVE
       ↓
┌─────────────────────────────────────┐
│      Inventory Domain (writer)       │
│  ┌────────────────────────────────┐ │
│  │  - InventoryLevel              │ │
│  │  - Reservations (subsystem)    │ │  ← CONFIRMED: Inventory writes on_hand, reserved
│  │  - Balance = on_hand - reserved│ │
│  └────────────────────────────────┘ │
│           ↓ logs                     │
│      StockMovement                   │
│  (RECEIPT, SHIPMENT, TRANSFER,      │
│   RESERVE, RELEASE, ADJUSTMENT,     │
│   WRITE_OFF, RETURN)                │
└─────────────────────────────────────┘
       ↑         ↑         ↑        ↑
    from      from     from    from
   Purchasing Orders Warehouse Returns
       
       
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Purchasing  │  │   Invoices   │  │   Payments   │
└──────────────┘  └──────────────┘  └──────────────┘
       │                  │              ↑ writes
       │ initiates        │              │
       → GoodsReceipt → Invoice → PaymentAttempt
       
       
┌──────────────┐  ┌──────────────┐
│  Warehouses  │  │  Suppliers   │
└──────────────┘  └──────────────┘
```

---

## Data Flow: Order to Shipment

```
Customer places order
    ↓
Orders.create_order()
    ├─ Validate customer (credit_limit)
    ├─ Validate items (sku exists, qty > 0)
    ├─ Check Inventory.available >= qty
    ├─ Create Order record
    └─ Emit event: "order.created"
           ↓
Inventory.on_order_created()
    ├─ For each item: RESERVE qty → Inventory.reserved += qty
    ├─ Create Reservation records
    ├─ Log: StockMovement (type=RESERVE)
    └─ Emit event: "reservation.created"
           ↓
Invoices.on_order_created()
    ├─ Create Invoice record (from Order.total)
    └─ Emit event: "invoice.created"
           ↓
Payments.on_invoice_created()
    ├─ Create PaymentAttempt (status=PENDING)
    ├─ Send to payment gateway
    └─ Emit event: "payment.initiated"
           ↓
    Payment gateway → callback: status=SUCCESS/FAILED
           ↓
Payments.on_payment_completed()
    ├─ Update PaymentAttempt.status = SUCCESS
    ├─ Emit event: "payment.success"
    └─ Update Invoice.status = PAID
           ↓
Orders.on_payment_success()
    ├─ Update Order.status = CONFIRMED
    ├─ Allow Warehouse to ship
    └─ Emit event: "order.ready_to_ship"
           ↓
Warehouse initiates shipment
    ├─ Create Shipment record
    └─ Emit event: "shipment.initiated"
           ↓
Inventory.on_shipment_initiated()
    ├─ SHIPMENT: on_hand -= qty, reserved -= qty
    ├─ Log: StockMovement (type=SHIPMENT)
    ├─ Release Reservation
    └─ Emit event: "shipment.completed"
           ↓
Orders.on_shipment_completed()
    ├─ Update Order.status = SHIPPED
    ├─ Generate tracking
    └─ Notify customer
```

---

## State Machines (per domain)

| Entity | States | Transitions |
|--------|--------|---|
| **Order** | DRAFT → PENDING → CONFIRMED → SHIPPED → DELIVERED / CANCELLED / FAILED | See docs/04-state-machines/order.md |
| **PaymentAttempt** | PENDING → SUCCESS / FAILED → REFUNDED | See docs/04-state-machines/payment_attempt.md |
| **Invoice** | DRAFT → ISSUED → PAID / OVERDUE / CANCELLED | See docs/04-state-machines/invoice.md |
| **Reservation** | ACTIVE → SHIPPED / RELEASED / PARTIALLY_SHIPPED | See docs/04-state-machines/reservation.md |
| **PurchaseOrder** | DRAFT → PENDING → RECEIVED → INVOICED → PAID / CANCELLED | See docs/04-state-machines/purchase_order.md |
| **Shipment** | DRAFT → IN_TRANSIT → DELIVERED / RETURNED | See docs/04-state-machines/warehouse_transfer.md |

---

## Database Schema (conceptual)

```
Tables per domain:

ORDERS domain:
  - order (id, customer_id, status, total, created_at)
  - order_line (id, order_id, sku, qty, price)
  - shipment (id, order_id, status, tracking)

INVENTORY domain:
  - inventory_level (id, warehouse_id, sku, on_hand, reserved)
  - stock_movement (id, warehouse_id, sku, type, qty_delta, reference_id, created_at)
  - reservation (id, order_id, sku, warehouse_id, qty, status)

PAYMENTS domain:
  - payment_attempt (id, invoice_id, amount, status, gateway_id)

INVOICES domain:
  - invoice (id, type: OUTBOUND/INBOUND, customer_id, total, status)
  - invoice_line (id, invoice_id, sku, qty, price)

AUDIT domain:
  - audit_log (id, entity_type, entity_id, action, old_value, new_value, user_id, timestamp)

... (more for Purchasing, Customers, Suppliers, Warehouses)
```

---

## Integration Points

### 1. With 1С (Accounting)
**Frequency**: Daily export + on-demand  
**Data**: StockMovement, Order totals, PaymentAttempt, Invoices  
**Format**: JSON API or flat file  
**Direction**: ERP → 1С (GL entries, tax reports)

### 2. With Payment Gateway (Stripe)
**Frequency**: Real-time  
**Data**: PaymentAttempt creation, webhook callbacks  
**Format**: REST API + webhook  
**Direction**: ERP ↔ Stripe (payments, refunds)

### 3. With Warehouse System (future)
**Frequency**: On demand  
**Data**: Shipment status, GoodsReceipt  
**Format**: TBD (currently manual)

---

## Constraints & Guarantees

### ACID Properties
- **Atomicity**: Transactions for critical operations (RESERVE, SHIPMENT, PAYMENT)
- **Consistency**: DB constraints (CHECK, UNIQUE, FK) + application validation
- **Isolation**: SERIALIZABLE for inventory, READ_COMMITTED for others
- **Durability**: PostgreSQL WAL

### Data Integrity
- Inventory balance = SUM(stock_movement) ✓
- PaymentAttempt.status = source of truth (not order.is_paid) ✓
- Audit log append-only (immutable) ✓
- All changes logged for compliance ✓

---

## Scalability & Performance

### Current (Foundation)
- Single PostgreSQL instance
- Synchronous API (no async jobs)
- In-memory caching (optional)

### Phase 2–3 (Growth)
- Read replicas for reporting
- Async jobs (APScheduler or Celery)
- Redis for caching / session
- Partitioning for large tables (stock_movement, audit_log)

### Phase 4 (Production)
- Kubernetes deployment
- Message queue (Kafka / RabbitMQ) for events
- CDN for static assets
- Load balancer + auto-scaling

---

## Security

- **Authentication**: JWT (users), OAuth (third-party integrations)
- **Authorization**: Role-based (RBAC): warehouse_manager, buyer, finance, admin
- **Secrets**: Environment variables / Kubernetes secrets (not in code)
- **PCI**: Payment data tokenized (not stored in ERP DB)
- **Audit**: All changes logged with user_id, timestamp
- **SQL Injection**: Parameterized queries (SQLAlchemy ORM)
- **CSRF**: CORS + SameSite cookies

---

## Monitoring & Observability

- **Logging**: Structured logs (JSON) to centralized sink (ELK, DataDog, etc.)
- **Metrics**: Request latency, error rates, DB query times (Prometheus)
- **Tracing**: Distributed tracing for cross-domain flows (Jaeger / DataDog)
- **Alerting**: PagerDuty for critical issues (payment failures, inventory inconsistency)
- **Dashboards**: Grafana for real-time visibility

---

## See Also

- `docs/02-domain/domain-map.md` — Domains and their relationships
- `docs/02-domain/cross-domain-flows.md` — Detailed workflows
- `docs/03-business-rules/registry.md` — Business rules (BR-xxx)
- `docs/04-state-machines/` — State machine definitions
- `docs/06-tech/stack-constraints.md` — Tech stack details
