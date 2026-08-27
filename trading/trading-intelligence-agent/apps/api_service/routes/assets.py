"""Asset and watchlist management routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from packages.core_models.pydantic_models import Asset, AssetCreate, WatchlistEntry
from packages.storage.database import get_db
from packages.storage.repositories import AssetRepository

router = APIRouter()


@router.get("", response_model=list[dict])
async def list_assets(
    asset_class: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    repo = AssetRepository(db)
    assets = await repo.get_all(asset_class=asset_class)
    return [
        {"id": a.id, "symbol": a.symbol, "name": a.name,
         "asset_class": a.asset_class, "exchange": a.exchange,
         "currency": a.currency, "sector": a.sector, "is_active": a.is_active}
        for a in assets
    ]


@router.post("", response_model=dict, status_code=201)
async def create_asset(
    asset: AssetCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    repo = AssetRepository(db)
    row = await repo.upsert(asset)
    return {"id": row.id, "symbol": row.symbol, "message": "Asset created/updated"}


@router.get("/watchlist", response_model=list[dict])
async def get_watchlist(db: AsyncSession = Depends(get_db)) -> list[dict]:
    repo = AssetRepository(db)
    assets = await repo.get_watchlist()
    return [
        {"id": a.id, "symbol": a.symbol, "name": a.name,
         "asset_class": a.asset_class, "exchange": a.exchange}
        for a in assets
    ]


@router.post("/watchlist", response_model=dict, status_code=201)
async def add_to_watchlist(
    body: dict,
    db: AsyncSession = Depends(get_db),
) -> dict:
    symbol = body.get("symbol", "").upper()
    notes = body.get("notes", "")
    if not symbol:
        raise HTTPException(status_code=422, detail="symbol is required")
    repo = AssetRepository(db)
    asset = await repo.get_by_symbol(symbol)
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {symbol} not found. Create it first via POST /assets")
    entry = await repo.add_to_watchlist(asset.id, notes=notes)
    return {"asset_id": asset.id, "symbol": symbol, "message": "Added to watchlist"}


@router.delete("/watchlist/{asset_id}", response_model=dict)
async def remove_from_watchlist(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    repo = AssetRepository(db)
    removed = await repo.remove_from_watchlist(asset_id)
    if not removed:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not on watchlist")
    return {"message": f"Removed asset {asset_id} from watchlist"}


@router.get("/{symbol}", response_model=dict)
async def get_asset(symbol: str, db: AsyncSession = Depends(get_db)) -> dict:
    repo = AssetRepository(db)
    asset = await repo.get_by_symbol(symbol.upper())
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {symbol} not found")
    return {
        "id": asset.id, "symbol": asset.symbol, "name": asset.name,
        "asset_class": asset.asset_class, "exchange": asset.exchange,
        "currency": asset.currency, "sector": asset.sector,
        "industry": asset.industry, "is_active": asset.is_active,
    }
