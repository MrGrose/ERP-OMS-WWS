import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from erp_oms_wms.db import Base
from erp_oms_wms.domains.audit import models as audit_models  # noqa: F401
from erp_oms_wms.domains.catalog import models as catalog_models  # noqa: F401
from erp_oms_wms.domains.customers import models as customer_models  # noqa: F401
from erp_oms_wms.domains.inventory import models as inventory_models  # noqa: F401
from erp_oms_wms.domains.invoices import models as invoice_models  # noqa: F401
from erp_oms_wms.domains.orders import models as order_models  # noqa: F401
from erp_oms_wms.domains.payments import models as payment_models  # noqa: F401
from erp_oms_wms.domains.pricing import models as pricing_models  # noqa: F401
from erp_oms_wms.domains.purchasing import models as purchasing_models  # noqa: F401
from erp_oms_wms.domains.returns import models as return_models  # noqa: F401
from erp_oms_wms.domains.suppliers import models as supplier_models  # noqa: F401
from erp_oms_wms.domains.transfers import models as transfer_models  # noqa: F401
from erp_oms_wms.domains.warehouses import models as warehouse_models  # noqa: F401


@pytest.fixture()
def db_session() -> Session:
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
