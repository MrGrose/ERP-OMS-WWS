# Returns, transfers, catalog, audit MVP

## Decision

- **Inventory** owns `transfer_stock` (paired TRANSFER movements) and `apply_return` (RETURN).
- **WarehouseTransfer** / **ReturnRequest** — document entities; completion calls inventory only from service layer.
- **Product**, **Supplier**, **Warehouse** — reference CRUD; PO still uses `supplier_id` string (FK validation later).
- **AuditLog** on catalog/supplier/transfer/return mutations; query via `/api/audit/logs`.
- **RBAC** — header `X-User-Role` (`Admin`, `Manager`, `WarehouseOperator`, `Accountant`); default `Admin` if omitted (dev).

## Out of scope (this slice)

- Full transfer SM (IN_TRANSIT, variance), return refund, pricing/customers, auth tokens.
