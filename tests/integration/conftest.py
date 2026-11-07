"""PostgreSQL integration fixtures: Alembic schema, disposable DB, isolated sessions."""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[2]

DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://erp:erp@localhost:5432/erp_oms_wms",
    ),
)


def alembic_upgrade_head(url: str) -> None:
    env = {**os.environ, "DATABASE_URL": url}
    alembic_ini = ROOT / "alembic.ini"
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", str(alembic_ini), "upgrade", "head"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"alembic upgrade failed:\n{result.stderr}\n{result.stdout}")


def truncate_public_schema(engine: Engine) -> None:
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public' AND tablename != 'alembic_version'
                ORDER BY tablename
                """
            )
        ).fetchall()
        if not rows:
            return
        names = ", ".join(f'"{r[0]}"' for r in rows)
        conn.execute(text(f"TRUNCATE {names} RESTART IDENTITY CASCADE"))


@pytest.fixture(scope="session")
def pg_database_url() -> str:
    return DATABASE_URL


@pytest.fixture(scope="session")
def pg_engine(pg_database_url: str) -> Generator[Engine, None, None]:
    alembic_upgrade_head(pg_database_url)
    engine = create_engine(pg_database_url, pool_pre_ping=True)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(pg_engine: Engine) -> Generator[Session, None, None]:
    connection = pg_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def pg_committed_session(pg_engine: Engine) -> Generator[Session, None, None]:
    """Independent connection with explicit commit (concurrency / multi-connection tests)."""
    connection = pg_engine.connect()
    session = Session(bind=connection)
    try:
        yield session
    finally:
        session.close()
        connection.close()
