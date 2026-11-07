from sqlalchemy import select

from erp_oms_wms.db import get_engine, session_scope
from erp_oms_wms.domains.payments.enums import PaymentAttemptStatus
from erp_oms_wms.domains.payments.models import PaymentAttempt


# Arq: счетчик pending попыток оплаты (reconcile stub, идемпотентно).
async def reconcile_payments(ctx: dict[str, object]) -> int:
    engine = get_engine()
    with session_scope(engine) as session:
        stmt = select(PaymentAttempt).where(PaymentAttempt.status == PaymentAttemptStatus.PENDING)
        return len(list(session.scalars(stmt)))
