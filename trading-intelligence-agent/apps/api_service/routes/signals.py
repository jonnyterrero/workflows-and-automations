"""Signal routes — list, retrieve, run, explain."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from packages.signal_engine.scorer import SignalScorer
from packages.core_models.pydantic_models import SignalHorizon
from packages.storage.database import get_db
from packages.storage.repositories import AssetRepository, SignalRepository

router = APIRouter()
_scorer = SignalScorer()


@router.get("")
async def list_signals(
    limit: int = Query(50, description="Max signals"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    repo = SignalRepository(db)
    signals = await repo.get_recent(limit=limit)
    return {
        "count": len(signals),
        "signals": [
            {
                "id": s.id, "asset_id": s.asset_id,
                "direction": s.direction, "score": s.score,
                "confidence": s.confidence, "horizon": s.horizon,
                "risk_flags": s.risk_flags or [],
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in signals
        ],
    }


@router.get("/{symbol}")
async def get_signals_for_symbol(
    symbol: str,
    limit: int = Query(10, description="Max signals"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    asset_repo = AssetRepository(db)
    asset = await asset_repo.get_by_symbol(symbol.upper())
    if not asset:
        raise HTTPException(404, f"Asset {symbol} not found")
    signal_repo = SignalRepository(db)
    signals = await signal_repo.get_by_asset(asset.id, limit=limit)
    return {
        "symbol": symbol.upper(),
        "count": len(signals),
        "signals": [
            {
                "id": s.id, "direction": s.direction, "score": s.score,
                "confidence": s.confidence, "horizon": s.horizon,
                "signal_type": s.signal_type, "reasoning": s.reasoning,
                "risk_flags": s.risk_flags or [],
                "counterarguments": s.counterarguments or [],
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in signals
        ],
    }


@router.post("/run")
async def run_signal(
    body: dict,
    db: AsyncSession = Depends(get_db),
) -> dict:
    symbol = body.get("symbol", "").upper()
    horizon_str = body.get("horizon", "swing")
    if not symbol:
        raise HTTPException(422, "symbol is required")

    try:
        horizon = SignalHorizon(horizon_str)
    except ValueError:
        horizon = SignalHorizon.SWING

    asset_repo = AssetRepository(db)
    asset = await asset_repo.get_by_symbol(symbol)
    if not asset:
        raise HTTPException(404, f"Asset {symbol} not found")

    signal_data = await _scorer.run_for_asset(
        asset_id=asset.id,
        symbol=symbol,
        asset_class=str(asset.asset_class),
        db=db,
        horizon=horizon,
    )
    signal_repo = SignalRepository(db)
    row = await signal_repo.create(signal_data)
    return {
        "signal_id": row.id,
        "symbol": symbol,
        "direction": row.direction,
        "score": row.score,
        "confidence": row.confidence,
        "reasoning": row.reasoning,
        "risk_flags": row.risk_flags or [],
        "counterarguments": row.counterarguments or [],
        "evidence_ids": row.evidence_ids or [],
        "disclaimer": "Signal is research output, NOT financial advice.",
    }


@router.get("/{signal_id}/evidence")
async def get_signal_evidence(
    signal_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    signal_repo = SignalRepository(db)
    signal = await signal_repo.get_by_id(signal_id)
    if not signal:
        raise HTTPException(404, f"Signal {signal_id} not found")
    return {
        "signal_id": signal_id,
        "evidence_ids": signal.evidence_ids or [],
        "reasoning": signal.reasoning,
        "counterarguments": signal.counterarguments or [],
        "risk_flags": signal.risk_flags or [],
    }
