import os
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


def get_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    return url


# Возвращает синхронный engine для PostgreSQL (или тестового URL).
def get_engine() -> Engine:
    return create_engine(get_database_url(), pool_pre_ping=True)


def get_session_factory(engine: Engine | None = None) -> sessionmaker[Session]:
    bind = engine or get_engine()
    return sessionmaker(bind=bind, autoflush=False, autocommit=False, expire_on_commit=False)


# Контекст сессии для скриптов и тестов.
@contextmanager
def session_scope(engine: Engine) -> Generator[Session, None, None]:
    factory = get_session_factory(engine)
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
