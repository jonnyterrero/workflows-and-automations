"""Canonical async database setup for the trading intelligence agent."""
from __future__ import annotations

import os
from collections.abc import AsyncIterator
from pathlib import Path

from sqlalchemy import event
from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from packages.core_models.db_tables import Base

DEFAULT_DATABASE_URL = "sqlite+aiosqlite:///./data/trading_intel.db"


def _database_url() -> str:
    raw = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    url = make_url(raw)
    if url.drivername.startswith("sqlite") and url.database and url.database not in (":memory:", ""):
        Path(url.database).parent.mkdir(parents=True, exist_ok=True)
    return raw


def _sqlite_connect_args(url: URL) -> dict[str, object]:
    if not url.drivername.startswith("sqlite"):
        return {}
    return {"check_same_thread": False}


def _build_engine() -> AsyncEngine:
    raw = _database_url()
    url = make_url(raw)
    engine = create_async_engine(
        raw,
        future=True,
        echo=os.getenv("SQL_ECHO", "false").lower() == "true",
        connect_args=_sqlite_connect_args(url),
    )

    if url.drivername.startswith("sqlite"):
        @event.listens_for(engine.sync_engine, "connect")
        def _enable_sqlite_fk(dbapi_connection, _connection_record) -> None:  # type: ignore[no-untyped-def]
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


engine = _build_engine()
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session


async def create_tables() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def dispose_engine() -> None:
    await engine.dispose()
