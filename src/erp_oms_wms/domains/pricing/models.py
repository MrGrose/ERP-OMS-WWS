from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from erp_oms_wms.db import Base
from erp_oms_wms.domains.pricing.enums import PriceList


class ProductPrice(Base):
    __tablename__ = "product_price"
    __table_args__ = (
        UniqueConstraint("price_list", "sku", name="uq_product_price_list_sku"),
        CheckConstraint("amount_cents >= 0", name="ck_product_price_nonneg"),
    )

    price_list: Mapped[PriceList] = mapped_column(
        Enum(PriceList, values_callable=lambda x: [e.value for e in x]),
        primary_key=True,
    )
    sku: Mapped[str] = mapped_column(String(128), primary_key=True)
    amount_cents: Mapped[int] = mapped_column(nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="RUB")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
