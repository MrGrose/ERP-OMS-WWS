from sqlalchemy.orm import Session

from erp_oms_wms.domains.pricing import service as pricing_service
from erp_oms_wms.domains.pricing.enums import PriceList
from erp_oms_wms.domains.suppliers.models import Supplier


def seed_retail_price(session: Session, sku: str, amount_cents: int = 1000) -> None:
    pricing_service.upsert_price(
        session, price_list=PriceList.RETAIL, sku=sku, amount_cents=amount_cents
    )


def ensure_supplier(
    session: Session, supplier_id: str, *, code: str = "SUP-1", name: str = "Supplier"
) -> None:
    if session.get(Supplier, supplier_id) is not None:
        return
    session.add(Supplier(id=supplier_id, code=code, name=name, is_active=True))
    session.flush()
