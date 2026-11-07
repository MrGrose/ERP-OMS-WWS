import asyncio
import os

from arq import create_pool
from arq.connections import RedisSettings

from erp_oms_wms.jobs.invoices import expire_invoices
from erp_oms_wms.jobs.notifications import send_notifications
from erp_oms_wms.jobs.payments import reconcile_payments
from erp_oms_wms.jobs.reports import generate_reports
from erp_oms_wms.jobs.reservations import release_expired_reservations
from erp_oms_wms.jobs.suppliers import sync_supplier_prices


class WorkerSettings:
    functions = [
        expire_invoices,
        release_expired_reservations,
        generate_reports,
        reconcile_payments,
        sync_supplier_prices,
        send_notifications,
    ]
    redis_settings = RedisSettings(
        host=os.environ.get("REDIS_HOST", "localhost"),
        port=int(os.environ.get("REDIS_PORT", "6379")),
    )


async def main() -> None:
    redis = await create_pool(WorkerSettings.redis_settings)
    await redis.enqueue_job("expire_invoices")
    await redis.close()


if __name__ == "__main__":
    asyncio.run(main())
