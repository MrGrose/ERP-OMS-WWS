# Ограничения стека и архитектурные решения

## Статус
**CONFIRMED**

## Выбранный стек

- **Backend**: Python 3.11+, FastAPI
- **ORM**: SQLAlchemy 2.x (без async для foundation phase)
- **Database**: PostgreSQL 14+ (for constraints, SERIALIZABLE, JSON)
- **Migrations**: Alembic
- **Testing**: pytest + fixtures
- **Frontend**: TypeScript, React, shadcn/ui + Tailwind

---

## Архитектурные ограничения

### 1. No nested services (CONFIRMED)
**Правило**: Код приложения в `src/<package>/`. Нет `src/services/`, `src/repositories/`, `src/utils/`.

**Обоснование**: Пока domain структура не определена, не разделять логику в отдельные каталоги.

**Когда пересмотреть**: После принятия решения в `docs/decisions/`

---

### 2. HTTP handlers are thin (CONFIRMED)
**Правило**: HTTP handler принимает запрос и отдает ответ. Бизнес-логика и расчеты — в функции того же пакета.

**Пример**:
```python
# orders/handler.py (thin)
@app.post("/orders")
def create_order(req: CreateOrderRequest):
    order = create_order_service(req.customer_id, req.items)
    return order


# orders/service.py (thick)
def create_order_service(customer_id: str, items: list):
    # Валидация, резервирование, логика
    ...
```

---

### 3. No secrets in code (CONFIRMED)
**Правило**: Все sensitive данные (DB password, API keys, etc) — в environment variables / config service, не в коде.

**Инструменты**:
- `.env` для local development (git-ignored)
- Kubernetes secrets / AWS Secrets Manager для production

---

### 4. Database constraints > application logic (CONFIRMED)
**Правило**: Если можно выразить правило в БД (constraint, trigger, check), делать в БД, а не в коде.

**Примеры**:
- `on_hand >= 0` → CHECK constraint, не application validation
- `reserved <= on_hand` → CHECK constraint
- `stock_movement` append-only → TRIGGER или DB permission (DELETE denied)
- Uniqueness → UNIQUE constraint, не application check

---

### 5. Transactions at domain level (PROPOSED)
**Правило**: Транзакция обхватывает одну операцию домена (напр., RESERVE или SHIPMENT), не несколько.

**Пример**:
```python
# Good: atomic reservation
def reserve_inventory(order_id, items):
    with db.transaction():
        # Check + UPDATE + INSERT stock_movement
        ...


# Bad: transaction spans multiple services
def process_order(order_id):
    with db.transaction():
        reserve_inventory(...)
        create_invoice(...)  # Not related to inventory
        ...
```

---

### 6. Event-driven for cross-domain (PROPOSED)
**Правило**: Для взаимодействия между доменами используть events, не direct API calls.

**Пример**:
```python
# Bad: Orders calls Inventory directly
def create_order():
    inventory.reserve(sku, qty)  # Tight coupling


# Good: Orders emits event, Inventory listens
def create_order():
    emit_event("order.created", order_id=..., items=...)


# inventory/listener.py
@event_listener("order.created")
def on_order_created(event):
    reserve_inventory(event.order_id, event.items)
```

**Status**: PROPOSED (может быть sync polling на foundation phase)

---

### 7. Audit log for all changes (CONFIRMED)
**Правило**: Все CREATE, UPDATE, DELETE → AuditLog (trigger или ORM hook)

**Что логировать**:
- `entity_type`, `entity_id`, `action`, `old_value`, `new_value`, `user_id`, `timestamp`

---

### 8. No GL (General Ledger) in this repo (CONFIRMED)
**Правило**: Финансовые учеты (double-entry bookkeeping) — OUT_OF_SCOPE. 

**Альтернатива**: Export data → 1С / SAP / другая accounting система

---

## ORM специфика

### SQLAlchemy 2.x
- Используем `Session.begin()` для транзакций (не `Session.commit()` напрямую)
- Alembic для миграций (версионирование БД)
- Constraints через `CheckConstraint`, `UniqueConstraint`, `ForeignKey`

**Не делать**:
- Не создавать SQLAlchemy models в foundation phase (пока домены не утверждены)
- Не использовать ORM для сложной business logic (лучше stored procedures или service functions)

---

## Database specifics (PostgreSQL)

- **SERIALIZABLE transactions** для inventory operations (BR-004)
- **LISTEN/NOTIFY** для async events (будущее)
- **JSON fields** для flexible attributes (если нужно)
- **Triggers** для audit_log и stock_movement append-only
- **Partitioning** для больших таблиц (stock_movement, audit_log) на production

---

## Frontend specifics

- **React** + TypeScript: typed components
- **shadcn/ui** + **Tailwind**: consistent design system
- **No external animations**: simple, functional UI
- **Playwright tests** для smoke tests

---

## Testing strategy

- **Unit**: функции домена (inventory logic, payment validation)
- **Integration**: API endpoint + database (fixture-based)
- **E2E**: Playwright scenarios (happy path + error cases)

---

## OPEN вопросы

- [ ] Async/await: нужна ли async обработка? (сейчас sync)
- [ ] Event queue: использовать ли Kafka / RabbitMQ? (сейчас sync events)
- [ ] Caching: Redis для performance? (сейчас напрямую из БД)
- [ ] API versioning: как handle breaking changes? (v1, v2, etc)
- [ ] Rate limiting: нужна ли? (soonish)

---

## Ссылки

- `docs/02-domain/domain-map.md` — 12 доменов
- `docs/03-business-rules/registry.md` — бизнес-правила
- `docs/04-state-machines/` — state machines
