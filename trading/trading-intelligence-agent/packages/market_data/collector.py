"""Market data collector — orchestrates equity/ETF OHLCV ingestion."""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import Any

import structlog
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from packages.data_providers.base import BaseMarketDataProvider, ProviderError
from packages.storage.repositories import MarketPriceRepository, RawPayloadRepository

logger = structlog.get_logger()


class MarketDataCollector:
    def __init__(self, provider: BaseMarketDataProvider, db_session_factory: Any) -> None:
        self.provider = provider
        self.db_factory = db_session_factory
        self._log = logger.bind(provider=provider.config.name)

    def _normalize_bar(self, bar: dict[str, Any]) -> dict[str, Any]:
        return {
            "symbol": bar.get("symbol", ""),
            "timestamp": bar.get("timestamp", ""),
            "open": float(bar.get("open", 0) or 0),
            "high": float(bar.get("high", 0) or 0),
            "low": float(bar.get("low", 0) or 0),
            "close": float(bar.get("close", 0)),
            "volume": int(bar.get("volume", 0) or 0),
            "source": bar.get("source", self.provider.config.name),
            "interval": bar.get("interval", "1d"),
        }

    async def collect_watchlist(
        self, symbols: list[str], interval: str = "1d", lookback_days: int = 60,
    ) -> dict[str, Any]:
        end = datetime.now(tz=timezone.utc)
        start = end - timedelta(days=lookback_days)
        summary: dict[str, Any] = {}

        async with self.db_factory() as db:
            raw_repo = RawPayloadRepository(db)
            price_repo = MarketPriceRepository(db)
            for symbol in symbols:
                t0 = time.monotonic()
                try:
                    @retry(
                        retry=retry_if_exception_type(ProviderError),
                        stop=stop_after_attempt(self.provider.config.rate_limit.retry_max_attempts),
                        wait=wait_exponential(
                            multiplier=self.provider.config.rate_limit.retry_base_delay,
                            max=self.provider.config.rate_limit.retry_max_delay,
                        ),
                        reraise=True,
                    )
                    async def _fetch() -> list[dict]:
                        return await self.provider.fetch_ohlcv(symbol, interval, start, end)

                    bars = await _fetch()
                    await raw_repo.store(self.provider.config.name, "ohlcv", symbol, {"bars": bars})
                    normalized = [self._normalize_bar(b) for b in bars]
                    upserted = await price_repo.bulk_upsert(normalized)
                    ms = int((time.monotonic() - t0) * 1000)
                    self._log.info("ohlcv_collected", symbol=symbol, bars=len(bars), upserted=upserted, ms=ms)
                    summary[symbol] = {"bars_fetched": len(bars), "bars_upserted": upserted, "error": None}
                except Exception as exc:  # noqa: BLE001
                    ms = int((time.monotonic() - t0) * 1000)
                    self._log.error("ohlcv_failed", symbol=symbol, error=str(exc), ms=ms)
                    summary[symbol] = {"bars_fetched": 0, "bars_upserted": 0, "error": str(exc)}
            await db.commit()
        return summary

    async def collect_latest_quotes(self, symbols: list[str]) -> dict[str, Any]:
        summary: dict[str, Any] = {}
        async with self.db_factory() as db:
            raw_repo = RawPayloadRepository(db)
            price_repo = MarketPriceRepository(db)
            for symbol in symbols:
                t0 = time.monotonic()
                try:
                    quote = await self.provider.fetch_latest_quote(symbol)
                    ms = int((time.monotonic() - t0) * 1000)
                    if quote is None:
                        summary[symbol] = {"upserted": False, "error": "no quote"}
                        continue
                    await raw_repo.store(self.provider.config.name, "quote", symbol, quote)
                    upserted = await price_repo.bulk_upsert([self._normalize_bar(quote)])
                    self._log.info("quote_collected", symbol=symbol, close=quote.get("close"), ms=ms)
                    summary[symbol] = {"upserted": upserted > 0, "error": None}
                except Exception as exc:  # noqa: BLE001
                    summary[symbol] = {"upserted": False, "error": str(exc)}
            await db.commit()
        return summary

    async def run_daily_collection(self, symbols: list[str]) -> dict[str, Any]:
        self._log.info("daily_start", symbols=len(symbols))
        t0 = time.monotonic()
        historical = await self.collect_watchlist(symbols)
        quotes = await self.collect_latest_quotes(symbols)
        ms = int((time.monotonic() - t0) * 1000)
        self._log.info("daily_complete", symbols=len(symbols), ms=ms)
        return {"historical": historical, "quotes": quotes, "duration_ms": ms}
