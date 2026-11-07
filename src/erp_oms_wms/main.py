from fastapi import FastAPI

from erp_oms_wms.api.routers import (
    audit,
    catalog,
    customers,
    inventory,
    invoices,
    orders,
    payments,
    pricing,
    purchasing,
    reports,
    returns,
    suppliers,
    transfers,
    warehouses,
)

app = FastAPI(title="erp-oms-wms")
app.include_router(inventory.router, prefix="/api")
app.include_router(orders.router, prefix="/api")
app.include_router(invoices.router, prefix="/api")
app.include_router(payments.router, prefix="/api")
app.include_router(purchasing.router, prefix="/api")
app.include_router(catalog.router, prefix="/api")
app.include_router(suppliers.router, prefix="/api")
app.include_router(warehouses.router, prefix="/api")
app.include_router(transfers.router, prefix="/api")
app.include_router(returns.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(customers.router, prefix="/api")
app.include_router(pricing.router, prefix="/api")
app.include_router(reports.router, prefix="/api")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
