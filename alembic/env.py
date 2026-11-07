import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
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

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    return os.environ.get("DATABASE_URL", config.get_main_option("sqlalchemy.url"))


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
