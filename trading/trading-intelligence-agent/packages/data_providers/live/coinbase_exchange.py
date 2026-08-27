"""Coinbase Exchange public market-data provider for crypto."""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
import structlog

from packages.data_providers.base import (
    BaseCryptoProvider,
    ParseError,
    ProviderConfig,
    ProviderError,
    RateLimitConfig,
    RateLimitError,
)

logger = structlog.get_logger()

COINBASE_EXCHANGE_BASE = "https://api.exchange.coinbase.com"

_GRANULARITY_BY_INTERVAL = {
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "1h": 3600,
    "6h": 21600,
    "1d": 86400,
}


class CoinbaseExchangeCryptoProvider(BaseCryptoProvider):
    """Public Coinbase Exchange market data. No private trading auth used."""

    def __init__(self) -> None:
        super().__init__(ProviderConfig(
            name="coinbase_exchange",
            base_url=COINBASE_EXCHANGE_BASE,
            rate_limit=RateLimitConfig(requests_per_minute=120, retry_max_attempts=3),
            timeout_seconds=30.0,
            demo_mode=False,
        ))
        self._log = logger.bind(provider="coinbase_exchange")

    def _product_id(self, symbol: str) -> str:
        upper = symbol.upper()
        if "-" in upper:
            return upper
        return f"{upper}-USD"

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
            try:
                response = await client.get(
                    f"{self.config.base_url}{path}",
                    params=params,
                    headers={"User-Agent": "trading-intelligence-agent/0.1"},
                )
            except httpx.RequestError as exc:
                raise ProviderError(f"Coinbase Exchange request failed: {exc}") from exc

        if response.status_code == 429:
            raise RateLimitError("Coinbase Exchange rate limit exceeded")
        if response.status_code >= 400:
            raise ProviderError(f"Coinbase Exchange HTTP {response.status_code}: {response.text[:200]}")

        try:
            return response.json()
        except ValueError as exc:
            raise ParseError("Coinbase Exchange returned non-JSON response") from exc

    async def fetch_ohlcv(
        self,
        symbol: str,
        interval: str = "1d",
        limit: int = 60,
    ) -> list[dict[str, Any]]:
        granularity = _GRANULARITY_BY_INTERVAL.get(interval, 86400)
        capped_limit = min(max(limit, 1), 300)
        now = datetime.now(tz=timezone.utc)
        start = now - timedelta(seconds=granularity * capped_limit)
        payload = await self._get(
            f"/products/{self._product_id(symbol)}/candles",
            params={
                "granularity": granularity,
                "start": start.isoformat(),
                "end": now.isoformat(),
            },
        )
        if not isinstance(payload, list):
            raise ParseError("Coinbase candle response should be a list")

        bars: list[dict[str, Any]] = []
        for candle in payload:
            if not isinstance(candle, list) or len(candle) < 6:
                continue
            ts = datetime.fromtimestamp(int(candle[0]), tz=timezone.utc)
            bars.append({
                "symbol": symbol.upper(),
                "timestamp": ts.isoformat(),
                "open": float(candle[3]),
                "high": float(candle[2]),
                "low": float(candle[1]),
                "close": float(candle[4]),
                "volume": float(candle[5]),
                "source": "coinbase_exchange",
                "interval": interval,
            })
        bars.sort(key=lambda item: item["timestamp"])
        return bars[-capped_limit:]

    async def fetch_ticker(self, symbol: str) -> dict[str, Any] | None:
        payload = await self._get(f"/products/{self._product_id(symbol)}/ticker")
        price = float(payload.get("price", 0) or 0)
        if price <= 0:
            return None
        ts_raw = payload.get("time")
        ts = (
            datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00")).isoformat()
            if ts_raw else datetime.now(tz=timezone.utc).isoformat()
        )
        bid = float(payload.get("bid", price) or price)
        ask = float(payload.get("ask", price) or price)
        return {
            "symbol": symbol.upper(),
            "timestamp": ts,
            "open": price,
            "high": price,
            "low": price,
            "close": price,
            "bid": bid,
            "ask": ask,
            "spread": max(0.0, ask - bid),
            "volume": float(payload.get("volume", 0) or 0),
            "volume_24h": float(payload.get("volume", 0) or 0),
            "source": "coinbase_exchange",
            "interval": "spot",
        }

    async def fetch_order_book(self, symbol: str, depth: int = 10) -> dict[str, Any] | None:
        payload = await self._get(
            f"/products/{self._product_id(symbol)}/book",
            params={"level": 2},
        )
        bids = payload.get("bids") or []
        asks = payload.get("asks") or []
        return {
            "symbol": symbol.upper(),
            "bids": [
                {"price": float(row[0]), "size": float(row[1]), "num_orders": int(row[2])}
                for row in bids[:depth]
            ],
            "asks": [
                {"price": float(row[0]), "size": float(row[1]), "num_orders": int(row[2])}
                for row in asks[:depth]
            ],
            "source": "coinbase_exchange",
            "spread": (
                max(0.0, float(asks[0][0]) - float(bids[0][0]))
                if bids and asks else math.nan
            ),
        }
