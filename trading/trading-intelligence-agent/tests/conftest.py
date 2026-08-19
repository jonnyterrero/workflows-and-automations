"""Pytest configuration and shared fixtures."""
from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse

import pytest_asyncio

os.environ.setdefault("DEMO_MODE", "true")
DEFAULT_TEST_DB_PATH = Path(__file__).resolve().parents[1] / "data" / "test_trading_intel.db"
os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{DEFAULT_TEST_DB_PATH.as_posix()}")
os.environ.setdefault("LOG_LEVEL", "WARNING")


def _test_db_path() -> Path:
    url = os.environ.get("TEST_DATABASE_URL", os.environ["DATABASE_URL"])
    parsed = urlparse(url)
    raw_path = parsed.path.lstrip("/") if parsed.scheme.startswith("sqlite") else DEFAULT_TEST_DB_PATH.as_posix()
    path = Path(raw_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


TEST_DB_PATH = _test_db_path()


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
