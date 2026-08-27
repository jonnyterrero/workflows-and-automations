"""Scheduler service — runs the shared full daily ingestion job on a cron."""
from __future__ import annotations

import asyncio
import os

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

from packages.jobs.daily_ingestion import run_daily_ingestion_job
from packages.observability.logging import configure_logging
from packages.storage.database import AsyncSessionLocal, create_tables

load_dotenv()
configure_logging("scheduler")
logger = structlog.get_logger()

DAILY_CRON = os.getenv("DAILY_JOB_CRON", "0 6 * * *")


async def run_daily_collection() -> None:
    logger.info("daily_job_start")
    result = await run_daily_ingestion_job(AsyncSessionLocal)
    logger.info("daily_job_complete", duration_ms=result.get("duration_ms"))


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
