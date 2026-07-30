"""AI research routes — daily briefings, asset reports, and committee dossiers."""
from __future__ import annotations

import os
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from packages.ai_research.asset_report import AssetResearchReportGenerator
from packages.ai_research.briefing import DailyBriefingGenerator
from packages.investment_agents.models import InvestmentCommitteeDossier, ResearchRequest
from packages.investment_agents.orchestrator import InvestmentResearchOrchestrator
from packages.storage.database import AsyncSessionLocal, get_db
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
    return await generator.generate(briefing_date)


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
    return await generator.generate(symbol.upper())


@router.get("/asset/{symbol}/latest")
async def get_latest_asset_report(
    symbol: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    raise HTTPException(501, "Asset report storage not yet implemented. Use POST /research/asset/{symbol} to generate.")


@router.post("/committee", response_model=InvestmentCommitteeDossier)
async def run_investment_committee(
    request: ResearchRequest,
    offline_demo: bool = Query(default=False, description="Use deterministic local demo without model calls."),
) -> InvestmentCommitteeDossier:
    """Run Theme Scout, Evidence Analyst, Risk Analyst, and Committee Manager end to end."""
    orchestrator = InvestmentResearchOrchestrator()
    use_offline = offline_demo or os.getenv("DEMO_MODE", "false").lower() == "true"
    if use_offline:
        return await orchestrator.run_offline_demo(request)
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(503, "OPENAI_API_KEY is required unless offline_demo=true or DEMO_MODE=true.")
    return await orchestrator.run(request)
