from __future__ import annotations

from packages.storage.database import normalize_database_url


def test_normalize_render_postgres_url() -> None:
    raw = "postgresql://user:pass@host:5432/trading_intel"
    assert normalize_database_url(raw) == "postgresql+asyncpg://user:pass@host:5432/trading_intel"


def test_normalize_postgres_alias_url() -> None:
    raw = "postgres://user:pass@host:5432/trading_intel"
    assert normalize_database_url(raw) == "postgresql+asyncpg://user:pass@host:5432/trading_intel"


def test_normalize_leaves_async_sqlite_unchanged() -> None:
    raw = "sqlite+aiosqlite:///./data/trading_intel.db"
    assert normalize_database_url(raw) == raw


def test_normalize_leaves_asyncpg_url_unchanged() -> None:
    raw = "postgresql+asyncpg://user:pass@host:5432/trading_intel"
    assert normalize_database_url(raw) == raw


def test_normalize_psycopg2_url_to_asyncpg() -> None:
    raw = "postgresql+psycopg2://user:pass@host:5432/trading_intel"
    assert normalize_database_url(raw) == "postgresql+asyncpg://user:pass@host:5432/trading_intel"
