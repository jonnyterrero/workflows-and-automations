"""Worker service — AI research job runner."""
from __future__ import annotations

import asyncio
import os

import structlog

from packages.jobs.daily_research import run_daily_research_job
from packages.observability.logging import configure_logging
from packages.storage.database import AsyncSessionLocal, create_tables

configure_logging("worker")
logger = structlog.get_logger()

BRIEFING_INTERVAL = int(os.getenv("BRIEFING_INTERVAL_SECONDS", "86400"))  # 24h default


async def main() -> None:
    await create_tables()
    logger.info("worker_started")

    await run_daily_research_job(AsyncSessionLocal)

    while True:
        await asyncio.sleep(BRIEFING_INTERVAL)
        await run_daily_research_job(AsyncSessionLocal)


if __name__ == "__main__":
    asyncio.run(main())
