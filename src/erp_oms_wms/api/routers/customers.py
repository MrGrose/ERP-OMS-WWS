from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from erp_oms_wms.api import schemas
from erp_oms_wms.api.deps import get_db
from erp_oms_wms.api.rbac import UserRole, get_actor_id, require_permission
from erp_oms_wms.domains.customers import service as customer_service
from erp_oms_wms.domains.customers.errors import CustomerNotFoundError
from erp_oms_wms.domains.pricing.enums import PriceList

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=list[schemas.CustomerOut])
def list_customers(
    session: Session = Depends(get_db),
    _role: UserRole = Depends(require_permission("orders.read")),
) -> list[schemas.CustomerOut]:
    rows = customer_service.list_customers(session)
    return [
        schemas.CustomerOut(
            id=c.id,
            name=c.name,
            email=c.email,
            price_list=c.price_list.value,
            is_active=c.is_active,
        )
        for c in rows
    ]


@router.post("", response_model=schemas.CustomerOut, status_code=201)
def create_customer(
    body: schemas.CustomerCreateIn,
    session: Session = Depends(get_db),
    actor: str = Depends(get_actor_id),
    _role: UserRole = Depends(require_permission("orders.manage")),
) -> schemas.CustomerOut:
    try:
        pl = PriceList(body.price_list)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="invalid price_list") from exc
    customer = customer_service.create_customer(
        session,
        name=body.name,
        email=body.email,
        price_list=pl,
        actor=actor,
    )
    return schemas.CustomerOut(
        id=customer.id,
        name=customer.name,
        email=customer.email,
        price_list=customer.price_list.value,
        is_active=customer.is_active,
    )


@router.get("/{customer_id}", response_model=schemas.CustomerOut)
def get_customer(
    customer_id: str,
    session: Session = Depends(get_db),
    _role: UserRole = Depends(require_permission("orders.read")),
) -> schemas.CustomerOut:
    try:
        customer = customer_service.get_customer(session, customer_id)
    except CustomerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return schemas.CustomerOut(
        id=customer.id,
        name=customer.name,
        email=customer.email,
        price_list=customer.price_list.value,
        is_active=customer.is_active,
    )
