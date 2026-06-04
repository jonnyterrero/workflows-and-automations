"""Worker service — AI research job runner."""
from __future__ import annotations

import asyncio
import os

import structlog

from packages.observability.logging import configure_logging
from packages.storage.database import create_tables, AsyncSessionLocal
from packages.ai_research.briefing import DailyBriefingGenerator
from packages.storage.repositories import AssetRepository

configure_logging("worker")
logger = structlog.get_logger()

BRIEFING_INTERVAL = int(os.getenv("BRIEFING_INTERVAL_SECONDS", "86400"))  # 24h default


async def run_daily_briefing() -> None:
    logger.info("worker_generating_briefing")
    try:
        generator = DailyBriefingGenerator(AsyncSessionLocal)
        briefing = await generator.generate()
        logger.info("worker_briefing_complete", date=str(briefing.get("date")))
    except Exception as exc:  # noqa: BLE001
        logger.error("worker_briefing_failed", error=str(exc))


async def run_signals_for_watchlist() -> None:
    from packages.signal_engine.scorer import SignalScorer
    from packages.storage.repositories import SignalRepository
    scorer = SignalScorer()
    async with AsyncSessionLocal() as db:
        asset_repo = AssetRepository(db)
        watchlist = await asset_repo.get_watchlist()
        signal_repo = SignalRepository(db)
        for asset in watchlist:
            try:
                signal_data = await scorer.run_for_asset(
                    asset_id=asset.id,
                    symbol=asset.symbol,
                    asset_class=str(asset.asset_class),
                    db=db,
                )
                await signal_repo.create(signal_data)
                logger.info("signal_created", symbol=asset.symbol, score=signal_data.get("score"))
            except Exception as exc:  # noqa: BLE001
                logger.error("signal_failed", symbol=asset.symbol, error=str(exc))
        await db.commit()


async def main() -> None:
    await create_tables()
    logger.info("worker_started")

    await run_signals_for_watchlist()
    await run_daily_briefing()

    while True:
        await asyncio.sleep(BRIEFING_INTERVAL)
        await run_signals_for_watchlist()
        await run_daily_briefing()


if __name__ == "__main__":
    asyncio.run(main())
