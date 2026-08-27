"""Risk evaluation routes."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from packages.analytics.technicals import TechnicalAnalyzer
from packages.risk_engine.risk_flags import RiskEngine
from packages.storage.database import get_db
from packages.storage.repositories import (
    AssetRepository, MarketPriceRepository, NewsRepository, SocialPostRepository,
)

router = APIRouter()
_analyzer = TechnicalAnalyzer()
_risk = RiskEngine()


@router.get("/{symbol}")
async def get_risk_assessment(
    symbol: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    asset_repo = AssetRepository(db)
    asset = await asset_repo.get_by_symbol(symbol.upper())
    if not asset:
        raise HTTPException(404, f"Asset {symbol} not found")

    price_repo = MarketPriceRepository(db)
    prices = await price_repo.get_range(
        asset.id,
        start=datetime.now(tz=timezone.utc) - timedelta(days=60),
        end=datetime.now(tz=timezone.utc),
    )
    price_dicts = [
        {"close": p.close, "high": p.high or p.close, "low": p.low or p.close,
         "open": p.open or p.close, "volume": p.volume or 0}
        for p in prices
    ]
    tech = _analyzer.compute(price_dicts)
    vol = tech.get("vol_20d")

    news_repo = NewsRepository(db)
    social_repo = SocialPostRepository(db)
    news = await news_repo.get_by_symbol(symbol.upper(), limit=20, hours_back=72)
    posts = await social_repo.get_by_symbol(symbol.upper(), limit=20, hours_back=48)

    flags = await _risk.evaluate(symbol.upper(), str(asset.asset_class), tech, vol, news, posts, db)

    return {
        "symbol": symbol.upper(),
        "asset_class": asset.asset_class,
        "risk_flags": flags,
        "risk_count": len(flags),
        "volatility_20d": round(vol, 4) if vol else None,
        "rsi_14": tech.get("rsi_14"),
        "trend": tech.get("trend_direction"),
        "disclaimer": "Risk assessment is informational only, not financial advice.",
    }


@router.post("/run")
async def run_risk_assessment(body: dict, db: AsyncSession = Depends(get_db)) -> dict:
    symbol = body.get("symbol", "").upper()
    if not symbol:
        raise HTTPException(422, "symbol is required")
    return await get_risk_assessment(symbol, db)
