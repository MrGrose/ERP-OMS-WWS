import os
from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from erp_oms_wms.api.deps import get_db
from erp_oms_wms.db import Base
from erp_oms_wms.domains.inventory import models as inventory_models  # noqa: F401
from erp_oms_wms.domains.orders import models as order_models  # noqa: F401
from erp_oms_wms.domains.pricing import models as pricing_models  # noqa: F401
from erp_oms_wms.domains.pricing import service as pricing_service
from erp_oms_wms.domains.pricing.enums import PriceList

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

from erp_oms_wms.main import app  # noqa: E402

engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(engine)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db() -> Generator[Session, None, None]:
    session = TestingSession()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_create_and_reserve_flow() -> None:
    with TestingSession() as session:
        pricing_service.upsert_price(
            session, price_list=PriceList.RETAIL, sku="SKU-API", amount_cents=100
        )
        session.commit()
    client.post(
        "/api/inventory/receipts",
        json={
            "warehouse_id": "wh-1",
            "sku": "SKU-API",
            "quantity": 5,
            "reference_id": "gr-api",
        },
    )
    create = client.post(
        "/api/orders",
        json={
            "customer_id": None,
            "lines": [{"warehouse_id": "wh-1", "sku": "SKU-API", "quantity": 2}],
        },
    )
    assert create.status_code == 201
    order_id = create.json()["id"]
    assert client.post(f"/api/orders/{order_id}/confirm").status_code == 200
    reserve = client.post(f"/api/orders/{order_id}/reserve")
    assert reserve.status_code == 200
    assert reserve.json()["status"] == "RESERVED"
    level = client.get("/api/inventory/levels", params={"warehouse_id": "wh-1", "sku": "SKU-API"})
    assert level.json()["reserved"] == 2
    assert level.json()["available"] == 3
