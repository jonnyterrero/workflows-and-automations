"""Crypto data collector — ingests OHLCV, tickers, and order books."""
from __future__ import annotations

import time
from typing import Any

import structlog

from packages.data_providers.base import BaseCryptoProvider, ProviderError
from packages.storage.repositories import MarketPriceRepository, RawPayloadRepository

logger = structlog.get_logger()
DEFAULT_SYMBOLS = ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD"]


class CryptoDataCollector:
    def __init__(self, provider: BaseCryptoProvider, db_session_factory: Any) -> None:
        self.provider = provider
        self.db_factory = db_session_factory
        self._log = logger.bind(provider=provider.config.name)

    def _syms(self, symbols: list[str] | None) -> list[str]:
        return symbols or DEFAULT_SYMBOLS

    def _normalize_bar(self, bar: dict[str, Any]) -> dict[str, Any]:
        return {
            "symbol": bar.get("symbol", ""),
            "timestamp": bar.get("timestamp", ""),
            "open": float(bar.get("open", 0) or 0),
            "high": float(bar.get("high", 0) or 0),
            "low": float(bar.get("low", 0) or 0),
            "close": float(bar.get("close", 0)),
            "volume": float(bar.get("volume", 0) or 0),
            "source": bar.get("source", self.provider.config.name),
            "interval": bar.get("interval", "1d"),
        }

    async def collect_ohlcv(self, symbols: list[str] | None = None) -> dict[str, Any]:
        syms = self._syms(symbols)
        summary: dict[str, Any] = {}
        async with self.db_factory() as db:
            raw_repo = RawPayloadRepository(db)
            price_repo = MarketPriceRepository(db)
            for symbol in syms:
                t0 = time.monotonic()
                try:
                    candles = await self.provider.fetch_ohlcv(symbol)
                    ms = int((time.monotonic() - t0) * 1000)
                    await raw_repo.store(self.provider.config.name, "crypto_ohlcv", symbol, {"candles": candles})
                    normalized = [self._normalize_bar(c) for c in candles]
                    upserted = await price_repo.bulk_upsert(normalized)
                    self._log.info("crypto_ohlcv", symbol=symbol, candles=len(candles), upserted=upserted, ms=ms)
                    summary[symbol] = {"candles_fetched": len(candles), "candles_upserted": upserted, "error": None}
                except Exception as exc:  # noqa: BLE001
                    summary[symbol] = {"candles_fetched": 0, "candles_upserted": 0, "error": str(exc)}
            await db.commit()
        return summary

    async def collect_tickers(self, symbols: list[str] | None = None) -> dict[str, Any]:
        syms = self._syms(symbols)
        summary: dict[str, Any] = {}
        async with self.db_factory() as db:
            raw_repo = RawPayloadRepository(db)
            for symbol in syms:
                try:
                    ticker = await self.provider.fetch_ticker(symbol)
                    if ticker:
                        await raw_repo.store(self.provider.config.name, "crypto_ticker", symbol, ticker)
                        summary[symbol] = {"found": True, "close": ticker.get("close"), "error": None}
                    else:
                        summary[symbol] = {"found": False, "error": "no ticker"}
                except Exception as exc:  # noqa: BLE001
                    summary[symbol] = {"found": False, "error": str(exc)}
            await db.commit()
        return summary

    async def collect_order_books(self, symbols: list[str] | None = None) -> dict[str, Any]:
        syms = self._syms(symbols)
        summary: dict[str, Any] = {}
        async with self.db_factory() as db:
            raw_repo = RawPayloadRepository(db)
            for symbol in syms:
                try:
                    book = await self.provider.fetch_order_book(symbol)
                    if book:
                        await raw_repo.store(self.provider.config.name, "crypto_order_book", symbol, book)
                        summary[symbol] = {
                            "found": True,
                            "bid_levels": len(book.get("bids", [])),
                            "ask_levels": len(book.get("asks", [])),
                            "error": None,
                        }
                    else:
                        summary[symbol] = {"found": False, "error": "no book"}
                except Exception as exc:  # noqa: BLE001
                    summary[symbol] = {"found": False, "error": str(exc)}
            await db.commit()
        return summary

    async def run_daily_collection(self, symbols: list[str] | None = None) -> dict[str, Any]:
        syms = self._syms(symbols)
        t0 = time.monotonic()
        ohlcv = await self.collect_ohlcv(syms)
        tickers = await self.collect_tickers(syms)
        order_books = await self.collect_order_books(syms)
        ms = int((time.monotonic() - t0) * 1000)
        return {"ohlcv": ohlcv, "tickers": tickers, "order_books": order_books, "duration_ms": ms}
