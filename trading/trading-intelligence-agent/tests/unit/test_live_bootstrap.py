from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from packages.bootstrap.live_setup import bootstrap_live_environment, resolve_bootstrap_asset
from packages.core_models.db_tables import AssetTable, Base, PortfolioProfileTable, WatchlistTable


def test_resolve_bootstrap_asset_supports_spot_crypto_pair() -> None:
    asset = resolve_bootstrap_asset("BTC-USD")
    assert asset.symbol == "BTC-USD"
    assert asset.exchange == "CRYPTO"


@pytest.mark.asyncio
async def test_bootstrap_live_environment_creates_assets_and_watchlist() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    summary = await bootstrap_live_environment(
        session_factory,
        watchlist_symbols=["NVDA", "BTC-USD", "SOL-USD"],
        include_full_universe=False,
        reset_watchlist=False,
    )

    async with session_factory() as session:
        assets = list((await session.execute(select(AssetTable).order_by(AssetTable.symbol))).scalars().all())
        watchlist_rows = list((await session.execute(select(WatchlistTable))).scalars().all())
        profiles = list((await session.execute(select(PortfolioProfileTable))).scalars().all())

    assert summary["status"] == "complete"
    assert summary["full_universe_seeded"] is False
    assert {asset.symbol for asset in assets} == {"BTC-USD", "NVDA", "SOL-USD"}
    assert len(watchlist_rows) == 3
    assert len(profiles) == 1

    await engine.dispose()
