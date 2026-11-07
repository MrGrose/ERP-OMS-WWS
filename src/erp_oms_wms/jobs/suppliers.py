from erp_oms_wms.db import get_engine, session_scope
from erp_oms_wms.domains.suppliers import service as supplier_service


# Arq: refresh hook — перечитывает supplier products (идемпотентный no-op sync).
async def sync_supplier_prices(ctx: dict[str, object]) -> int:
    engine = get_engine()
    with session_scope(engine) as session:
        total = 0
        for supplier in supplier_service.list_suppliers(session):
            total += len(supplier_service.list_supplier_products(session, supplier.id))
        return total
