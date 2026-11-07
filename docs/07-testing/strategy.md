# Тестовая стратегия

## Статус
**PROPOSED**

## Назначение
Определение типов тестов, инструментов, критериев покрытия для ERP.

---

## Пирамида тестов

```
        /\
       /  \  E2E (Playwright)
      / 5% \
     /______\
      /    \
     /      \  Integration (pytest + DB)
    / 25%    \
   /________\
    /      \
   /        \  Unit (pytest)
  / 70%      \
 /____________\
```

---

## Unit Tests (70%)

### Инструменты
- **Framework**: pytest
- **Fixtures**: conftest.py (setup/teardown)
- **Mocking**: unittest.mock, monkeypatch

### Тестируемое
- Business logic functions (inventory calculations, validations)
- Domain rules (BR-xxx)
- State machine transitions

### Пример: Inventory Reserve

```python
# tests/inventory/test_reserve.py
import pytest
from erp.inventory.service import reserve_inventory
from erp.inventory.exceptions import InsufficientStock


def test_reserve_available_stock(inventory_level):
    """Test: Reserve when stock is available"""
    # Arrange
    inventory_level.on_hand = 100
    inventory_level.reserved = 0

    # Act
    result = reserve_inventory(sku="SKU-001", warehouse_id="WH-001", qty=50)

    # Assert
    assert result.reserved == 50
    assert inventory_level.available == 50


def test_reserve_insufficient_stock(inventory_level):
    """Test: Cannot reserve more than available"""
    # Arrange
    inventory_level.on_hand = 100
    inventory_level.reserved = 60

    # Act & Assert
    with pytest.raises(InsufficientStock):
        reserve_inventory(sku="SKU-001", warehouse_id="WH-001", qty=50)
```

---

## Integration Tests (25%)

### Инструменты
- **Framework**: pytest
- **Database**: Test DB (PostgreSQL on Docker)
- **Fixtures**: Transactional fixtures (rollback after test)

### Тестируемое
- API endpoints (HTTP layer)
- Database constraints
- Cross-domain flows

### Пример: Order to Shipment Flow

```python
# tests/orders/test_order_to_shipment.py
import pytest
from erp.orders.handler import create_order, ship_order
from erp.orders.models import Order
from erp.inventory.models import InventoryLevel


@pytest.fixture
def order_with_inventory(db, customer_factory, inventory_factory):
    """Setup: Customer, Inventory, Order"""
    customer = customer_factory(credit_limit=5000)
    inventory = inventory_factory(sku="SKU-001", on_hand=100)

    order = create_order({"customer_id": customer.id, "items": [{"sku": "SKU-001", "qty": 50}]})

    yield order, inventory
    db.session.rollback()


def test_order_to_shipment_flow(order_with_inventory):
    """Test: Full flow from order creation to shipment"""
    order, inventory = order_with_inventory

    # Assert: Order created, reservation made
    assert order.status == "CONFIRMED"
    assert inventory.reserved == 50

    # Act: Ship order
    shipment = ship_order(order.id)

    # Assert: on_hand decreased, reserved freed
    inventory_refreshed = db.query(InventoryLevel).filter_by(sku="SKU-001").one()
    assert inventory_refreshed.on_hand == 50  # 100 - 50
    assert inventory_refreshed.reserved == 0  # freed
    assert shipment.status == "SHIPPED"
```

---

## E2E Tests (5%)

### Инструменты
- **Framework**: Playwright
- **Browser**: Chromium
- **Coverage**: Happy path + critical errors

### Тестируемое
- Full user workflows (GUI + API + DB)
- UI responsiveness
- Accessibility basics

### Пример: Create Order via UI

```python
# tests/e2e/test_order_creation.py
import pytest
from playwright.sync_api import Page


@pytest.fixture
def browser_page():
    """Setup: Browser, login"""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://localhost:3000/login")
        page.fill("[name=email]", "user@example.com")
        page.fill("[name=password]", "password123")
        page.click("[type=submit]")
        yield page
        browser.close()


def test_create_order_full_flow(browser_page: Page):
    """Test: Create order via UI"""
    # Navigate to orders page
    browser_page.goto("http://localhost:3000/orders")

    # Click "New Order"
    browser_page.click('button:has-text("New Order")')

    # Fill form
    browser_page.fill("[name=customer_id]", "CUST-001")
    browser_page.click('[data-sku="SKU-001"]')
    browser_page.fill("[name=qty]", "50")

    # Submit
    browser_page.click("button[type=submit]")

    # Assert: Order created, redirect to order details
    assert "orders/" in browser_page.url
    assert browser_page.is_visible("text=Order created successfully")
```

---

## Критерии покрытия

| Уровень | Минимум | Цель |
|---------|---------|------|
| Lines | 60% | 80% |
| Branches | 50% | 70% |
| Functions | 70% | 90% |
| Statements | 60% | 80% |

**Command**:
```bash
pytest --cov=erp --cov-report=html
# Open htmlcov/index.html to view report
```

---

## Тестовые данные (Fixtures)

### Factory pattern

```python
# tests/factories.py
import factory
from erp.customers.models import Customer


class CustomerFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Customer

    name = factory.Faker("name")
    email = factory.Faker("email")
    credit_limit = 5000


# Usage in tests
customer = CustomerFactory(name="John Doe")
```

---

## Continuous Integration

### GitHub Actions workflow

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements-dev.txt
      - run: pytest --cov=erp
      - run: npm test (frontend)
```

---

## Performance Tests (Future)

```python
# tests/performance/test_inventory_reserve_throughput.py
import pytest
from time import time


def test_concurrent_reserves(stress_data):
    """Test: 1000 concurrent RESERVE operations"""
    start = time()

    # Simulate 1000 concurrent requests
    for i in range(1000):
        reserve_inventory(sku="SKU-001", qty=1)

    duration = time() - start

    # Assert: < 5 seconds
    assert duration < 5.0, f"Took {duration}s, expected < 5s"
```

---

## OPEN вопросы

- [ ] Load testing tools (Locust / k6)?
- [ ] Contract testing (API compatibility)?
- [ ] Chaos engineering (fault injection)?
- [ ] Test data cleanup strategy (fixtures vs DB reset)?
