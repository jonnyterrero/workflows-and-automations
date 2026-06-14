"""Pytest configuration and shared fixtures."""
from __future__ import annotations

import os
from pathlib import Path

import pytest_asyncio

TEST_DB_PATH = Path(__file__).resolve().parents[1] / "data" / "test_trading_intel.db"
TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

os.environ.setdefault("DEMO_MODE", "true")
os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{TEST_DB_PATH.as_posix()}")
os.environ.setdefault("LOG_LEVEL", "WARNING")


@pytest_asyncio.fixture(scope="session", autouse=True)
async def init_database():
    from packages.storage.database import create_tables

    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    await create_tables()
    yield


@pytest_asyncio.fixture
async def db_session(init_database):
    from packages.storage.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        yield session
