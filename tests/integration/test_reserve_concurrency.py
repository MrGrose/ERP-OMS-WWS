import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from erp_oms_wms.db import Base
from erp_oms_wms.domains.inventory import service as inventory_service
from erp_oms_wms.domains.inventory.errors import InsufficientAvailableError
from erp_oms_wms.domains.inventory.models import InventoryLevel
from erp_oms_wms.domains.orders import service as order_service
from erp_oms_wms.domains.orders.errors import InvalidOrderTransitionError
from erp_oms_wms.domains.pricing import service as pricing_service
from erp_oms_wms.domains.pricing.enums import PriceList

pytestmark = pytest.mark.integration

DATABASE_URL = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")


@pytest.fixture(scope="module")
def pg_engine():
    if not DATABASE_URL or not DATABASE_URL.startswith("postgresql"):
        pytest.skip("TEST_DATABASE_URL или DATABASE_URL (postgresql) не задан")
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


# Два параллельных reserve на последнюю единицу: один успех, один отказ (BR).
def test_concurrent_reserve_last_unit(pg_engine) -> None:
    factory = sessionmaker(bind=pg_engine, autoflush=False, autocommit=False)

    def seed() -> None:
        session = factory()
        try:
            pricing_service.upsert_price(
                session, price_list=PriceList.RETAIL, sku="SKU-LAST", amount_cents=100
            )
            inventory_service.apply_receipt(session, "wh-conc", "SKU-LAST", 1, "setup", "seed")
            session.commit()
        finally:
            session.close()

    seed()

    def try_reserve(order_suffix: str) -> str:
        session = factory()
        try:
            order = order_service.create_draft_order(
                session,
                customer_id=None,
                lines=[{"warehouse_id": "wh-conc", "sku": "SKU-LAST", "quantity": 1}],
            )
            order_service.confirm_order(session, order.id)
            order_service.reserve_order(session, order.id)
            session.commit()
            return f"ok-{order_suffix}"
        except (InsufficientAvailableError, InvalidOrderTransitionError):
            session.rollback()
            return f"fail-{order_suffix}"
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    outcomes: list[str] = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(try_reserve, str(i)) for i in range(2)]
        for f in as_completed(futures):
            outcomes.append(f.result())

    assert outcomes.count("ok-0") + outcomes.count("ok-1") == 1
    assert outcomes.count("fail-0") + outcomes.count("fail-1") == 1

    session = factory()
    try:
        level = session.scalars(
            select(InventoryLevel).where(
                InventoryLevel.warehouse_id == "wh-conc",
                InventoryLevel.sku == "SKU-LAST",
            ),
        ).one()
        assert level.on_hand == 1
        assert level.reserved == 1
        assert level.available == 0
    finally:
        session.close()
