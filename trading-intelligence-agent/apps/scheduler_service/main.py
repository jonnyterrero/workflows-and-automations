"""Scheduler service — runs daily and intraday data collection jobs."""
from __future__ import annotations

import asyncio
import os

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from packages.observability.logging import configure_logging
from packages.storage.database import create_tables, AsyncSessionLocal
from packages.data_providers.demo.market import DemoMarketDataProvider
from packages.data_providers.demo.news import DemoNewsProvider
from packages.data_providers.demo.macro import DemoMacroProvider
from packages.data_providers.demo.crypto import DemoCryptoProvider
from packages.market_data.collector import MarketDataCollector
from packages.macro_data.collector import MacroDataCollector
from packages.crypto_exchanges.collector import CryptoDataCollector
from packages.news_intel.collector import NewsCollector
from packages.storage.repositories import AssetRepository

configure_logging("scheduler")
logger = structlog.get_logger()

DAILY_CRON = os.getenv("DAILY_JOB_CRON", "0 6 * * *")
DEFAULT_WATCHLIST = os.getenv(
    "DEFAULT_WATCHLIST", "SPY,QQQ,TLT,AAPL,NVDA,TSLA,BTC-USD,ETH-USD"
).split(",")


async def run_daily_collection() -> None:
    logger.info("daily_job_start")
    async with AsyncSessionLocal() as db:
        asset_repo = AssetRepository(db)
        watchlist = await asset_repo.get_watchlist()
        symbols = [a.symbol for a in watchlist] or DEFAULT_WATCHLIST

    equity = [s for s in symbols if "-USD" not in s]
    crypto = [s for s in symbols if "-USD" in s]

    if equity:
        collector = MarketDataCollector(DemoMarketDataProvider(), AsyncSessionLocal)
        result = await collector.run_daily_collection(equity)
        logger.info("market_collection_done", summary=list(result.keys()))

    macro_c = MacroDataCollector(DemoMacroProvider(), AsyncSessionLocal)
    await macro_c.collect_all_indicators()
    await macro_c.collect_yield_curve()

    if crypto:
        crypto_c = CryptoDataCollector(DemoCryptoProvider(), AsyncSessionLocal)
        await crypto_c.run_daily_collection(crypto)

    news_c = NewsCollector([DemoNewsProvider()], AsyncSessionLocal)
    await news_c.collect_for_watchlist(symbols)
    logger.info("daily_job_complete")


async def main() -> None:
    await create_tables()
    scheduler = AsyncIOScheduler()

    parts = DAILY_CRON.split()
    if len(parts) == 5:
        minute, hour, day, month, dow = parts
        scheduler.add_job(
            run_daily_collection,
            CronTrigger(minute=minute, hour=hour, day=day, month=month, day_of_week=dow),
            id="daily_collection",
        )

    scheduler.start()
    logger.info("scheduler_started", cron=DAILY_CRON)

    # Run immediately on startup
    await run_daily_collection()

    try:
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("scheduler_stopped")


if __name__ == "__main__":
    asyncio.run(main())
