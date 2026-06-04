"""AI research routes — daily briefings and asset reports."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from packages.ai_research.briefing import DailyBriefingGenerator
from packages.ai_research.asset_report import AssetResearchReportGenerator
from packages.storage.database import get_db, AsyncSessionLocal
from packages.storage.repositories import DailyBriefingRepository

router = APIRouter()


@router.post("/daily-briefing")
async def generate_daily_briefing(
    body: dict | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    briefing_date_str = (body or {}).get("date")
    briefing_date = date.fromisoformat(briefing_date_str) if briefing_date_str else None
    generator = DailyBriefingGenerator(AsyncSessionLocal)
    briefing = await generator.generate(briefing_date)
    return briefing


@router.get("/daily-briefing/latest")
async def get_latest_daily_briefing(db: AsyncSession = Depends(get_db)) -> dict:
    repo = DailyBriefingRepository(db)
    row = await repo.get_latest()
    if not row:
        raise HTTPException(404, "No daily briefing found. Run POST /research/daily-briefing first.")
    return {
        "id": row.id,
        "date": row.date,
        "market_regime_summary": row.market_regime_summary,
        "macro_summary": row.macro_summary,
        "equity_summary": row.equity_summary,
        "etf_summary": row.etf_summary,
        "bond_summary": row.bond_summary,
        "crypto_summary": row.crypto_summary,
        "top_opportunities": row.top_opportunities or [],
        "top_risks": row.top_risks or [],
        "major_news_events": row.major_news_events or [],
        "evidence_ids": row.evidence_ids or [],
        "disclaimer": row.disclaimer,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


@router.post("/asset/{symbol}")
async def generate_asset_report(
    symbol: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    generator = AssetResearchReportGenerator(AsyncSessionLocal)
    report = await generator.generate(symbol.upper())
    return report


@router.get("/asset/{symbol}/latest")
async def get_latest_asset_report(
    symbol: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    raise HTTPException(501, "Asset report storage not yet implemented. Use POST /research/asset/{symbol} to generate.")
