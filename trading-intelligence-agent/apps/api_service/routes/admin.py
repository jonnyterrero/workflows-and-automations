"""Admin / dev operation routes."""
from __future__ import annotations

import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from packages.data_providers.factory import (
    get_crypto_provider,
    get_macro_provider,
    get_market_provider,
    get_news_providers,
    get_social_providers,
    provider_status,
)
from packages.data_providers.live.x_setup import get_x_config, verify_x_bearer
from packages.market_data.collector import MarketDataCollector
from packages.macro_data.collector import MacroDataCollector
from packages.crypto_exchanges.collector import CryptoDataCollector
from packages.news_intel.collector import NewsCollector
from packages.social_intel.collector import SocialCollector
from packages.storage.database import get_db, AsyncSessionLocal
from packages.storage.repositories import AssetRepository

load_dotenv()
router = APIRouter()

DEFAULT_WATCHLIST = os.getenv(
    "DEFAULT_WATCHLIST", "SPY,QQQ,TLT,AAPL,NVDA,TSLA,BTC-USD,ETH-USD"
).split(",")
DEFAULT_CRYPTO_WATCHLIST = os.getenv(
    "DEFAULT_CRYPTO_WATCHLIST", "BTC-USD,ETH-USD,SOL-USD"
).split(",")


@router.get("/setup/x")
async def x_api_setup_guide() -> dict:
    """X API setup instructions and current configuration status."""
    return get_x_config()


@router.post("/setup/x/verify")
async def x_api_verify() -> dict:
    """Test X_BEARER_TOKEN against the recent-search endpoint."""
    return await verify_x_bearer()


@router.get("/providers")
async def list_providers() -> dict:
    """Show which data providers are active."""
    return provider_status()


@router.post("/jobs/run-daily")
async def run_daily_job(db: AsyncSession = Depends(get_db)) -> dict:
    """Run a full daily data collection cycle."""
    t0 = datetime.now(tz=timezone.utc)
    asset_repo = AssetRepository(db)
    watchlist = await asset_repo.get_watchlist()
    symbols = [a.symbol for a in watchlist] or DEFAULT_WATCHLIST

    equity_symbols = [s for s in symbols if "-USD" not in s]
    crypto_symbols = [s for s in symbols if "-USD" in s] or DEFAULT_CRYPTO_WATCHLIST

    market_result = {}
    macro_result = {}
    crypto_result = {}
    news_result = {}
    social_result = {}

    if equity_symbols:
        collector = MarketDataCollector(get_market_provider(), AsyncSessionLocal)
        market_result = await collector.run_daily_collection(equity_symbols)

    macro_collector = MacroDataCollector(get_macro_provider(), AsyncSessionLocal)
    macro_result = await macro_collector.collect_all_indicators()
    yield_result = await macro_collector.collect_yield_curve()

    if crypto_symbols:
        crypto_collector = CryptoDataCollector(get_crypto_provider(), AsyncSessionLocal)
        crypto_result = await crypto_collector.run_daily_collection(crypto_symbols)

    news_collector = NewsCollector(get_news_providers(), AsyncSessionLocal)
    news_result = await news_collector.collect_for_watchlist(symbols)
    crypto_news_result = await news_collector.collect_crypto_headlines(hours_back=48)

    social_collector = SocialCollector(get_social_providers(), AsyncSessionLocal)
    social_result = await social_collector.collect_for_watchlist(symbols)

    duration_ms = int((datetime.now(tz=timezone.utc) - t0).total_seconds() * 1000)
    return {
        "status": "complete",
        "duration_ms": duration_ms,
        "providers": provider_status(),
        "market": market_result,
        "macro_indicators": list(macro_result.keys()),
        "yield_curve": yield_result,
        "crypto": crypto_result,
        "news": news_result,
        "crypto_news": crypto_news_result,
        "social": social_result,
    }


@router.post("/jobs/run-ingestion")
async def run_ingestion(db: AsyncSession = Depends(get_db)) -> dict:
    return await run_daily_job(db)


@router.get("/jobs/status")
async def get_job_status() -> dict:
    return {
        "status": "no background job running",
        "providers": provider_status(),
        "note": "Use POST /admin/jobs/run-daily to trigger",
    }
