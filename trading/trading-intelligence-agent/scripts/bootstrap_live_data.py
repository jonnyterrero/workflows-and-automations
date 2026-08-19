"""Initialize a live-ready database without seeding demo fixtures."""
from __future__ import annotations

import argparse
import asyncio
import json

from dotenv import load_dotenv

from packages.bootstrap.live_setup import bootstrap_live_environment
from packages.observability.logging import configure_logging
from packages.storage.database import AsyncSessionLocal


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap live assets, watchlist, and default portfolio policy.")
    parser.add_argument(
        "--watchlist",
        default="",
        help="Comma-separated watchlist override. Defaults to DEFAULT_WATCHLIST from the environment.",
    )
    parser.add_argument(
        "--watchlist-only",
        action="store_true",
        help="Only create the watchlist assets instead of the full configured asset universe.",
    )
    parser.add_argument(
        "--reset-watchlist",
        action="store_true",
        help="Clear existing watchlist entries before adding the target watchlist.",
    )
    return parser.parse_args()


async def _main() -> None:
    args = _parse_args()
    watchlist = [symbol.strip().upper() for symbol in args.watchlist.split(",") if symbol.strip()] or None
    summary = await bootstrap_live_environment(
        AsyncSessionLocal,
        watchlist_symbols=watchlist,
        include_full_universe=not args.watchlist_only,
        reset_watchlist=args.reset_watchlist,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    load_dotenv()
    configure_logging("bootstrap-live")
    asyncio.run(_main())
