from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from erp_oms_wms.db import Base
from erp_oms_wms.domains.inventory.models import new_uuid_str
from erp_oms_wms.domains.payments.enums import PaymentAttemptStatus


class PaymentAttempt(Base):
    __tablename__ = "payment_attempt"
    __table_args__ = (UniqueConstraint("external_event_id", name="uq_payment_external_event_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid_str)
    invoice_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("invoice.id"),
        nullable=False,
        index=True,
    )
    status: Mapped[PaymentAttemptStatus] = mapped_column(
        Enum(PaymentAttemptStatus, values_callable=lambda x: [e.value for e in x]),
        default=PaymentAttemptStatus.CREATED,
    )
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="RUB")
    provider: Mapped[str] = mapped_column(String(64), nullable=False, default="mock")
    external_payment_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    external_event_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
