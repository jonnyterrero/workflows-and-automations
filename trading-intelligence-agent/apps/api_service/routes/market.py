"""Market data routes."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from packages.analytics.technicals import TechnicalAnalyzer
from packages.storage.database import get_db
from packages.storage.repositories import AssetRepository, MarketPriceRepository

router = APIRouter()
_analyzer = TechnicalAnalyzer()


@router.get("/{symbol}/prices")
async def get_prices(
    symbol: str,
    interval: str = Query("1d", description="Bar interval"),
    days: int = Query(60, description="Lookback days"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    asset_repo = AssetRepository(db)
    asset = await asset_repo.get_by_symbol(symbol.upper())
    if not asset:
        raise HTTPException(404, f"Asset {symbol} not found")

    price_repo = MarketPriceRepository(db)
    end = datetime.now(tz=timezone.utc)
    start = end - timedelta(days=days)
    prices = await price_repo.get_range(asset.id, start, end, interval=interval)
    return {
        "symbol": symbol.upper(),
        "interval": interval,
        "count": len(prices),
        "prices": [
            {
                "timestamp": p.timestamp.isoformat(),
                "open": p.open, "high": p.high, "low": p.low,
                "close": p.close, "volume": p.volume,
            }
            for p in prices
        ],
    }


@router.get("/{symbol}/latest")
async def get_latest_price(symbol: str, db: AsyncSession = Depends(get_db)) -> dict:
    asset_repo = AssetRepository(db)
    asset = await asset_repo.get_by_symbol(symbol.upper())
    if not asset:
        raise HTTPException(404, f"Asset {symbol} not found")
    price_repo = MarketPriceRepository(db)
    latest = await price_repo.get_latest(asset.id)
    if not latest:
        raise HTTPException(404, f"No price data for {symbol}")
    return {
        "symbol": symbol.upper(),
        "timestamp": latest.timestamp.isoformat(),
        "close": latest.close,
        "open": latest.open,
        "high": latest.high,
        "low": latest.low,
        "volume": latest.volume,
        "source": latest.source,
    }


@router.get("/{symbol}/candles")
async def get_candles_with_technicals(
    symbol: str,
    days: int = Query(60, description="Lookback days"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    asset_repo = AssetRepository(db)
    asset = await asset_repo.get_by_symbol(symbol.upper())
    if not asset:
        raise HTTPException(404, f"Asset {symbol} not found")
    price_repo = MarketPriceRepository(db)
    end = datetime.now(tz=timezone.utc)
    start = end - timedelta(days=days)
    prices = await price_repo.get_range(asset.id, start, end)
    price_dicts = [
        {"close": p.close, "high": p.high or p.close, "low": p.low or p.close,
         "open": p.open or p.close, "volume": p.volume or 0, "timestamp": p.timestamp.isoformat()}
        for p in prices
    ]
    technicals = _analyzer.compute(price_dicts)
    return {
        "symbol": symbol.upper(),
        "bars": price_dicts,
        "technicals": technicals,
    }
