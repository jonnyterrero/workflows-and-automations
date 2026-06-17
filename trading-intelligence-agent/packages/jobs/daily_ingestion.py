"""Shared orchestration for the full daily ingestion cycle."""
from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

from packages.bootstrap.live_setup import bootstrap_live_environment
from packages.corporate_intel.collector import CorporateIntelCollector
from packages.crypto_exchanges.collector import CryptoDataCollector
from packages.data_providers.factory import (
    get_crypto_provider,
    get_filings_provider,
    get_fundamentals_provider,
    get_macro_provider,
    get_market_provider,
    get_news_providers,
    get_social_providers,
    provider_status,
)
from packages.macro_data.collector import MacroDataCollector
from packages.market_data.collector import MarketDataCollector
from packages.news_intel.collector import NewsCollector
from packages.social_intel.collector import SocialCollector
from packages.storage.database import create_tables
from packages.storage.repositories import AssetRepository

DEFAULT_WATCHLIST = os.getenv(
    "DEFAULT_WATCHLIST",
    "VOO,VXUS,QQQM,SMH,NLR,GLD,IBIT,SGOV,BTC-USD,ETH-USD",
).split(",")
DEFAULT_CRYPTO_WATCHLIST = os.getenv(
    "DEFAULT_CRYPTO_WATCHLIST",
    "BTC-USD,ETH-USD,SOL-USD",
).split(",")


async def _ensure_bootstrapped(db_session_factory: Any) -> dict[str, Any] | None:
    await create_tables()
    async with db_session_factory() as db:
        asset_repo = AssetRepository(db)
        assets = await asset_repo.get_all()
        watchlist = await asset_repo.get_watchlist()

    if assets and watchlist:
        return None

    return await bootstrap_live_environment(
        db_session_factory,
        include_full_universe=True,
        reset_watchlist=False,
    )


async def _resolve_symbols(db_session_factory: Any) -> list[str]:
    async with db_session_factory() as db:
        asset_repo = AssetRepository(db)
        watchlist = await asset_repo.get_watchlist()
        return [asset.symbol for asset in watchlist] or [symbol.strip() for symbol in DEFAULT_WATCHLIST if symbol.strip()]


async def run_daily_ingestion_job(db_session_factory: Any) -> dict[str, Any]:
    t0 = datetime.now(tz=UTC)
    bootstrap_summary = await _ensure_bootstrapped(db_session_factory)
    symbols = await _resolve_symbols(db_session_factory)
    equity_symbols = [symbol for symbol in symbols if "-USD" not in symbol.upper()]
    crypto_symbols = [symbol for symbol in symbols if "-USD" in symbol.upper()] or [
        symbol.strip() for symbol in DEFAULT_CRYPTO_WATCHLIST if symbol.strip()
    ]

    market_result: dict[str, Any] = {}
    macro_result: dict[str, Any] = {}
    crypto_result: dict[str, Any] = {}
    news_result: dict[str, Any] = {}
    general_news_result: dict[str, Any] = {}
    social_result: dict[str, Any] = {}
    corporate_result: dict[str, Any] = {}

    if equity_symbols:
        market_collector = MarketDataCollector(get_market_provider(), db_session_factory)
        market_result = await market_collector.run_daily_collection(equity_symbols)

    macro_collector = MacroDataCollector(get_macro_provider(), db_session_factory)
    macro_result = await macro_collector.collect_all_indicators()
    yield_result = await macro_collector.collect_yield_curve()

    if crypto_symbols:
        crypto_collector = CryptoDataCollector(get_crypto_provider(), db_session_factory)
        crypto_result = await crypto_collector.run_daily_collection(crypto_symbols)

    news_collector = NewsCollector(get_news_providers(), db_session_factory)
    news_result = await news_collector.collect_for_watchlist(symbols)
    general_news_result = await news_collector.collect_general_market_news(hours_back=24)
    crypto_news_result = await news_collector.collect_crypto_headlines(hours_back=48)

    social_collector = SocialCollector(get_social_providers(), db_session_factory)
    social_result = await social_collector.collect_for_watchlist(symbols)

    corporate_collector = CorporateIntelCollector(
        get_fundamentals_provider(),
        get_filings_provider(),
        db_session_factory,
    )
    corporate_result = await corporate_collector.collect_for_symbols(symbols)

    duration_ms = int((datetime.now(tz=UTC) - t0).total_seconds() * 1000)
    return {
        "status": "complete",
        "duration_ms": duration_ms,
        "bootstrap": bootstrap_summary,
        "providers": provider_status(),
        "market": market_result,
        "macro_indicators": list(macro_result.keys()),
        "yield_curve": yield_result,
        "crypto": crypto_result,
        "news": news_result,
        "general_news": general_news_result,
        "crypto_news": crypto_news_result,
        "social": social_result,
        "corporate": corporate_result,
    }
