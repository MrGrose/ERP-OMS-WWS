# Backend MVP closure (TZ §14–§23)

## Decision

- **Pricing** — `ProductPrice` + customer `price_list`; цена на строку заказа при `confirm`, сумма счёта по строкам если `amount_cents` не передан.
- **Customers** — CRUD `/api/customers`.
- **Supplier products** — `SupplierProduct` + валидация `supplier_id` на PO.
- **Reporting** — `/api/reports/*` (stock, movements, sales, purchases, unpaid, supplier balances, turnover).
- **Inventory API** — `/api/inventory/movements`, `/reservations`.
- **Partial ship** — `ship_reservation_quantity`, `POST …/lines/{id}/ship`, `POST …/complete` (SHIPPED→COMPLETED).
- **Auth** — `require_permission` по матрице ролей (заголовок `X-User-Role`).
- **Jobs** — все имена из ТЗ зарегистрированы в Arq worker (часть — идемпотентные агрегаты/счётчики).

## Still OUT_OF_SCOPE

- JWT/OAuth, BI, GL, полные SM transfer/return/refund, RAG, frontend.
