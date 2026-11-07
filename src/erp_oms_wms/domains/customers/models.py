import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from erp_oms_wms.db import Base
from erp_oms_wms.domains.pricing.enums import PriceList


def new_uuid_str() -> str:
    return str(uuid.uuid4())


class Customer(Base):
    __tablename__ = "customer"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid_str)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    email: Mapped[str | None] = mapped_column(String(256), nullable=True)
    price_list: Mapped[PriceList] = mapped_column(
        Enum(PriceList, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=PriceList.RETAIL,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
