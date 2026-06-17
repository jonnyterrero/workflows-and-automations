"""Collector service — intraday crypto and market data collection."""
from __future__ import annotations

import asyncio
import os

import structlog

from packages.crypto_exchanges.collector import CryptoDataCollector
from packages.data_providers.factory import get_crypto_provider
from packages.observability.logging import configure_logging
from packages.storage.database import AsyncSessionLocal, create_tables

configure_logging("collector")
logger = structlog.get_logger()

REFRESH_INTERVAL = int(os.getenv("INTRADAY_REFRESH_INTERVAL", "300"))
CRYPTO_SYMBOLS = os.getenv("DEFAULT_WATCHLIST", "VOO,VXUS,QQQM,SMH,NLR,GLD,IBIT,SGOV,BTC-USD,ETH-USD").split(",")
CRYPTO_SYMBOLS = [s for s in CRYPTO_SYMBOLS if "-USD" in s]


async def run_intraday_loop() -> None:
    collector = CryptoDataCollector(get_crypto_provider(), AsyncSessionLocal)
    while True:
        try:
            logger.info("intraday_collection_tick", symbols=CRYPTO_SYMBOLS)
            await collector.collect_tickers(CRYPTO_SYMBOLS)
        except Exception as exc:  # noqa: BLE001
            logger.error("intraday_collection_error", error=str(exc))
        await asyncio.sleep(REFRESH_INTERVAL)


async def main() -> None:
    await create_tables()
    logger.info("collector_started", interval=REFRESH_INTERVAL, crypto=CRYPTO_SYMBOLS)
    await run_intraday_loop()


if __name__ == "__main__":
    asyncio.run(main())
