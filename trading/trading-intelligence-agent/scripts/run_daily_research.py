"""Run the shared daily research job from CLI or cron."""
from __future__ import annotations

import asyncio
import json

from dotenv import load_dotenv

from packages.jobs.daily_research import run_daily_research_job
from packages.observability.logging import configure_logging
from packages.storage.database import AsyncSessionLocal


async def _main() -> None:
    result = await run_daily_research_job(AsyncSessionLocal)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    load_dotenv()
    configure_logging("daily-research-cli")
    asyncio.run(_main())
