"""Backtesting routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from packages.backtesting.replay import SignalReplayer
from packages.storage.database import get_db, AsyncSessionLocal
from packages.storage.repositories import AssetRepository

router = APIRouter()


@router.post("/signal-strategy")
async def backtest_signal_strategy(
    body: dict,
    db: AsyncSession = Depends(get_db),
) -> dict:
    symbol = body.get("symbol", "").upper()
    lookforward_days = int(body.get("lookforward_days", 5))
    if not symbol:
        raise HTTPException(422, "symbol is required")

    asset_repo = AssetRepository(db)
    asset = await asset_repo.get_by_symbol(symbol)
    if not asset:
        raise HTTPException(404, f"Asset {symbol} not found")

    replayer = SignalReplayer(AsyncSessionLocal)
    results = await replayer.replay_asset(
        asset_id=asset.id,
        symbol=symbol,
        lookforward_days=lookforward_days,
    )
    return results


@router.get("/results/{backtest_id}")
async def get_backtest_results(backtest_id: int) -> dict:
    raise HTTPException(
        501,
        "Persistent backtest result storage not yet implemented. "
        "Use POST /backtest/signal-strategy for live replay.",
    )
