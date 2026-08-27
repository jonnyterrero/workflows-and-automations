"""Shared orchestration for daily watchlist signals and briefing generation."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from packages.bootstrap.live_setup import bootstrap_live_environment
from packages.ai_research.briefing import DailyBriefingGenerator
from packages.signal_engine.scorer import SignalScorer
from packages.storage.database import create_tables
from packages.storage.repositories import AssetRepository, SignalRepository


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


async def run_daily_research_job(db_session_factory: Any) -> dict[str, Any]:
    t0 = datetime.now(tz=UTC)
    scorer = SignalScorer()
    signal_rows: list[dict[str, Any]] = []
    bootstrap_summary = await _ensure_bootstrapped(db_session_factory)

    async with db_session_factory() as db:
        asset_repo = AssetRepository(db)
        signal_repo = SignalRepository(db)
        watchlist = await asset_repo.get_watchlist()

        for asset in watchlist:
            signal_data = await scorer.run_for_asset(
                asset_id=asset.id,
                symbol=asset.symbol,
                asset_class=str(asset.asset_class),
                db=db,
            )
            row = await signal_repo.create(signal_data)
            signal_rows.append({
                "signal_id": row.id,
                "symbol": asset.symbol,
                "direction": row.direction,
                "score": row.score,
                "confidence": row.confidence,
            })
        await db.commit()

    briefing_generator = DailyBriefingGenerator(db_session_factory)
    briefing = await briefing_generator.generate()
    duration_ms = int((datetime.now(tz=UTC) - t0).total_seconds() * 1000)
    return {
        "status": "complete",
        "duration_ms": duration_ms,
        "bootstrap": bootstrap_summary,
        "signals_generated": len(signal_rows),
        "signals": signal_rows,
        "briefing_date": str(briefing.get("date")),
    }
