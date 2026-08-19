"""Admin / dev operation routes."""
from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from packages.data_providers.factory import (
    get_fundamentals_provider,
    provider_status,
)
from packages.data_providers.live.crypto_feeds_catalog import catalog_summary
from packages.data_providers.live.iposcoop_calendar import IPOScoopCalendarProvider
from packages.data_providers.live.x_setup import get_x_config, verify_x_bearer
from packages.bootstrap.live_setup import bootstrap_live_environment
from packages.jobs.daily_ingestion import run_daily_ingestion_job
from packages.jobs.daily_research import run_daily_research_job
from packages.security.admin import require_admin_api_token
from packages.storage.database import AsyncSessionLocal, get_db
from packages.storage.repositories import FilingRepository, ModelFeatureRepository

load_dotenv()
router = APIRouter(dependencies=[Depends(require_admin_api_token)])


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
async def run_daily_job() -> dict:
    """Run a full daily data collection cycle."""
    return await run_daily_ingestion_job(AsyncSessionLocal)


@router.post("/jobs/bootstrap-live")
async def bootstrap_live_job() -> dict:
    """Seed the live asset universe, watchlist, and default portfolio policy."""
    return await bootstrap_live_environment(
        AsyncSessionLocal,
        include_full_universe=True,
        reset_watchlist=False,
    )


@router.post("/jobs/run-ingestion")
async def run_ingestion() -> dict:
    return await run_daily_job()


@router.post("/jobs/run-research")
async def run_research_job() -> dict:
    return await run_daily_research_job(AsyncSessionLocal)


@router.get("/jobs/status")
async def get_job_status() -> dict:
    return {
        "status": "no background job running",
        "providers": provider_status(),
        "note": "Use POST /admin/jobs/run-daily or POST /admin/jobs/run-research to trigger",
    }
