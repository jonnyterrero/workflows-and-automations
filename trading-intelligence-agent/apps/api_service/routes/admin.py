"""Admin / dev operation routes."""
from __future__ import annotations

import os
from datetime import UTC, datetime

from dotenv import load_dotenv
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

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
from packages.data_providers.live.crypto_feeds_catalog import catalog_summary
from packages.data_providers.live.iposcoop_calendar import IPOScoopCalendarProvider
from packages.data_providers.live.x_setup import get_x_config, verify_x_bearer
from packages.macro_data.collector import MacroDataCollector
from packages.market_data.collector import MarketDataCollector
from packages.news_intel.collector import NewsCollector
from packages.social_intel.collector import SocialCollector
from packages.storage.database import AsyncSessionLocal, get_db
from packages.storage.repositories import AssetRepository, FilingRepository, ModelFeatureRepository

load_dotenv()
router = APIRouter()

DEFAULT_WATCHLIST = os.getenv(
    "DEFAULT_WATCHLIST", "SPY,QQQ,TLT,AAPL,NVDA,TSLA,BTC-USD,ETH-USD"
).split(",")
DEFAULT_CRYPTO_WATCHLIST = os.getenv(
    "DEFAULT_CRYPTO_WATCHLIST", "BTC-USD,ETH-USD,SOL-USD"
).split(",")


@router.get("/crypto-sources")
async def crypto_sources_catalog() -> dict:
    """Curated crypto RSS catalog + pending API integrations (Glassnode, DeFiLlama, etc.)."""
    return catalog_summary()


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


@router.get("/corporate/{symbol}")
async def get_corporate_intel(
    symbol: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    feature_repo = ModelFeatureRepository(db)
    filing_repo = FilingRepository(db)
    latest = await feature_repo.get_latest(symbol.upper())
    filings = await filing_repo.get_recent_by_symbol(symbol.upper(), limit=10, days_back=120)
    return {
        "symbol": symbol.upper(),
        "latest_features": latest.features_json if latest else None,
        "feature_timestamp": latest.timestamp.isoformat() if latest else None,
        "recent_filings": [
            {
                "filing_type": row.filing_type,
                "filed_at": row.filed_at.isoformat() if row.filed_at else None,
                "url": row.url,
                "accession_number": row.accession_number,
                "summary": row.summary,
            }
            for row in filings
        ],
    }


@router.get("/ipo-calendar")
async def get_ipo_calendar() -> dict:
    sources: list[str] = []
    ipos: list[dict] = []
    seen: set[tuple[str, str, str]] = set()

    def _add_items(items: list[dict], source_name: str) -> None:
        for item in items:
            symbol = str(item.get("symbol") or "").upper()
            name = str(item.get("name") or "")
            event_date = str(item.get("date") or "")
            dedupe_key = (symbol, name, event_date)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            merged = dict(item)
            merged.setdefault("source", source_name)
            ipos.append(merged)

    provider = get_fundamentals_provider()
    if provider is not None and hasattr(provider, "fetch_ipo_calendar"):
        sources.append(provider.config.name)
        _add_items(await provider.fetch_ipo_calendar(), provider.config.name)

    if os.getenv("ENABLE_IPOSCOOP_SCRAPER", "true").lower() == "true":
        iposcoop = IPOScoopCalendarProvider()
        sources.append(iposcoop.config.name)
        _add_items(await iposcoop.fetch_ipo_calendar(), iposcoop.config.name)

    if not ipos:
        return {"configured": False, "ipos": [], "sources": [], "error": "No IPO calendar providers configured"}

    ipos.sort(key=lambda item: (str(item.get("date") or "9999-12-31"), str(item.get("symbol") or "")))
    return {"configured": True, "count": len(ipos), "sources": sources, "ipos": ipos}


@router.post("/jobs/run-daily")
async def run_daily_job(db: AsyncSession = Depends(get_db)) -> dict:
    """Run a full daily data collection cycle."""
    t0 = datetime.now(tz=UTC)
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
    general_news_result = await news_collector.collect_general_market_news(hours_back=24)
    crypto_news_result = await news_collector.collect_crypto_headlines(hours_back=48)

    social_collector = SocialCollector(get_social_providers(), AsyncSessionLocal)
    social_result = await social_collector.collect_for_watchlist(symbols)

    corporate_collector = CorporateIntelCollector(
        get_fundamentals_provider(),
        get_filings_provider(),
        AsyncSessionLocal,
    )
    corporate_result = await corporate_collector.collect_for_symbols(symbols)

    duration_ms = int((datetime.now(tz=UTC) - t0).total_seconds() * 1000)
    return {
        "status": "complete",
        "duration_ms": duration_ms,
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
