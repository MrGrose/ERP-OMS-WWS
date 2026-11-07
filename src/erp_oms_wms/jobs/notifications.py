from erp_oms_wms.db import get_engine, session_scope
from erp_oms_wms.domains.invoices import service as invoice_service


# Arq: MVP-заглушка - только считает просроченные счета (без реальной отправки)
async def send_notifications(ctx: dict[str, object]) -> int:
    engine = get_engine()
    with session_scope(engine) as session:
        return invoice_service.expire_due_invoices(session)
