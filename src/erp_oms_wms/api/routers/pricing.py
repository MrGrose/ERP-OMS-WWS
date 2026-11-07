from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from erp_oms_wms.api import schemas
from erp_oms_wms.api.deps import get_db
from erp_oms_wms.api.rbac import UserRole, require_permission
from erp_oms_wms.domains.pricing import service as pricing_service
from erp_oms_wms.domains.pricing.enums import PriceList

router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.get("/prices", response_model=list[schemas.ProductPriceOut])
def list_prices(
    price_list: str | None = None,
    session: Session = Depends(get_db),
    _role: UserRole = Depends(require_permission("catalog.read")),
) -> list[schemas.ProductPriceOut]:
    pl = None
    if price_list is not None:
        try:
            pl = PriceList(price_list)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="invalid price_list") from exc
    rows = pricing_service.list_prices(session, price_list=pl)
    return [
        schemas.ProductPriceOut(
            price_list=r.price_list.value,
            sku=r.sku,
            amount_cents=r.amount_cents,
            currency=r.currency,
        )
        for r in rows
    ]


@router.put("/prices", response_model=schemas.ProductPriceOut)
def upsert_price(
    body: schemas.ProductPriceUpsertIn,
    session: Session = Depends(get_db),
    _role: UserRole = Depends(require_permission("catalog.write")),
) -> schemas.ProductPriceOut:
    try:
        pl = PriceList(body.price_list)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="invalid price_list") from exc
    row = pricing_service.upsert_price(
        session,
        price_list=pl,
        sku=body.sku,
        amount_cents=body.amount_cents,
        currency=body.currency,
    )
    return schemas.ProductPriceOut(
        price_list=row.price_list.value,
        sku=row.sku,
        amount_cents=row.amount_cents,
        currency=row.currency,
    )
