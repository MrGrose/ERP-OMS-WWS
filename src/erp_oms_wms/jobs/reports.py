from erp_oms_wms.db import get_engine, session_scope
from erp_oms_wms.domains.reporting import service as reporting_service


# Arq: прогон агрегатов reporting (observable count строк).
async def generate_reports(ctx: dict[str, object]) -> int:
    engine = get_engine()
    with session_scope(engine) as session:
        stock = len(reporting_service.current_stock(session))
        sales = len(reporting_service.sales_summary(session))
        unpaid = len(reporting_service.unpaid_invoices(session))
        return stock + sales + unpaid
