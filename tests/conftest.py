from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import erp_oms_wms.domains.audit.models as audit_models  # noqa: F401
import erp_oms_wms.domains.catalog.models as catalog_models  # noqa: F401
import erp_oms_wms.domains.customers.models as customer_models  # noqa: F401
import erp_oms_wms.domains.inventory.models as inventory_models  # noqa: F401
import erp_oms_wms.domains.invoices.models as invoice_models  # noqa: F401
import erp_oms_wms.domains.orders.models as order_models  # noqa: F401
import erp_oms_wms.domains.payments.models as payment_models  # noqa: F401
import erp_oms_wms.domains.pricing.models as pricing_models  # noqa: F401
import erp_oms_wms.domains.purchasing.models as purchasing_models  # noqa: F401
import erp_oms_wms.domains.returns.models as return_models  # noqa: F401
import erp_oms_wms.domains.suppliers.models as supplier_models  # noqa: F401
import erp_oms_wms.domains.transfers.models as transfer_models  # noqa: F401
import erp_oms_wms.domains.warehouses.models as warehouse_models  # noqa: F401
from erp_oms_wms.db import Base


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()
