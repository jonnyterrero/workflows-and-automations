"""Admin / dev operation routes."""
from __future__ import annotations

import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from packages.data_providers.demo.market import DemoMarketDataProvider
from packages.data_providers.demo.news import DemoNewsProvider
from packages.data_providers.demo.social import DemoSocialProvider
from packages.data_providers.demo.macro import DemoMacroProvider
from packages.data_providers.demo.crypto import DemoCryptoProvider
from packages.market_data.collector import MarketDataCollector
from packages.macro_data.collector import MacroDataCollector
from packages.crypto_exchanges.collector import CryptoDataCollector
from packages.news_intel.collector import NewsCollector
from packages.storage.database import get_db, AsyncSessionLocal
from packages.storage.repositories import AssetRepository

router = APIRouter()

DEFAULT_WATCHLIST = os.getenv(
    "DEFAULT_WATCHLIST", "SPY,QQQ,TLT,AAPL,NVDA,TSLA,BTC-USD,ETH-USD"
).split(",")


@router.post("/jobs/run-daily")
async def run_daily_job(db: AsyncSession = Depends(get_db)) -> dict:
    """Run a full daily data collection cycle."""
    t0 = datetime.now(tz=timezone.utc)
    asset_repo = AssetRepository(db)
    watchlist = await asset_repo.get_watchlist()
    symbols = [a.symbol for a in watchlist] or DEFAULT_WATCHLIST

    equity_symbols = [s for s in symbols if "-USD" not in s]
    crypto_symbols = [s for s in symbols if "-USD" in s]

    market_result = {}
    macro_result = {}
    crypto_result = {}
    news_result = {}

    # Market data
    if equity_symbols:
        collector = MarketDataCollector(DemoMarketDataProvider(), AsyncSessionLocal)
        market_result = await collector.run_daily_collection(equity_symbols)

    # Macro data
    macro_collector = MacroDataCollector(DemoMacroProvider(), AsyncSessionLocal)
    macro_result = await macro_collector.collect_all_indicators()
    yield_result = await macro_collector.collect_yield_curve()

    # Crypto data
    if crypto_symbols:
        crypto_collector = CryptoDataCollector(DemoCryptoProvider(), AsyncSessionLocal)
        crypto_result = await crypto_collector.run_daily_collection(crypto_symbols)

    # News and social
    news_collector = NewsCollector([DemoNewsProvider()], AsyncSessionLocal)
    news_result = await news_collector.collect_for_watchlist(symbols)

    social_collector = NewsCollector([DemoSocialProvider()], AsyncSessionLocal)  # type: ignore

    duration_ms = int((datetime.now(tz=timezone.utc) - t0).total_seconds() * 1000)
    return {
        "status": "complete",
        "duration_ms": duration_ms,
        "market": market_result,
        "macro_indicators": list(macro_result.keys()),
        "crypto": crypto_result,
        "news": news_result,
    }


@router.post("/jobs/run-ingestion")
async def run_ingestion(db: AsyncSession = Depends(get_db)) -> dict:
    return await run_daily_job(db)


@router.get("/jobs/status")
async def get_job_status() -> dict:
    return {"status": "no background job running", "note": "Use POST /admin/jobs/run-daily to trigger"}
