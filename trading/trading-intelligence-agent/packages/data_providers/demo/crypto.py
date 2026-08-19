"""Demo crypto provider — synthetic crypto data."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np
import structlog

from packages.data_providers.base import BaseCryptoProvider, ProviderConfig

logger = structlog.get_logger()

_BASES: dict[str, float] = {
    "BTC-USD": 67_000.0, "ETH-USD": 3_400.0, "SOL-USD": 170.0, "BNB-USD": 580.0,
}


def _timestamps(n: int) -> list[datetime]:
    now = datetime.now(tz=timezone.utc).replace(second=0, microsecond=0)
    return [now - timedelta(days=n - 1 - i) for i in range(n)]


class DemoCryptoProvider(BaseCryptoProvider):
    def __init__(self) -> None:
        super().__init__(ProviderConfig(name="demo_crypto", demo_mode=True))

    def _seed(self, symbol: str) -> int:
        return abs(hash(symbol)) % (2**31)

    def _candles(self, symbol: str, n: int, interval: str) -> list[dict[str, Any]]:
        base = _BASES.get(symbol, 100.0)
        rng = np.random.default_rng(self._seed(symbol))
        returns = rng.normal(0.0003, 0.03, n)
        timestamps = _timestamps(n)
        bars = []
        close = base
        for i, ts in enumerate(timestamps):
            open_p = close
            close = round(open_p * (1 + returns[i]), 2)
            high = round(max(open_p, close) * (1 + abs(rng.normal(0, 0.005))), 2)
            low = round(min(open_p, close) * (1 - abs(rng.normal(0, 0.005))), 2)
            vol = round(float(rng.uniform(100.0, 5000.0)), 4)
            bars.append({
                "symbol": symbol, "timestamp": ts.isoformat(),
                "open": round(open_p, 2), "high": high, "low": low,
                "close": close, "volume": vol,
                "source": "demo", "interval": interval,
            })
        return bars

    async def fetch_ohlcv(self, symbol: str, interval: str = "1d", limit: int = 60) -> list[dict[str, Any]]:
        return self._candles(symbol, limit, interval)

    async def fetch_ticker(self, symbol: str) -> dict[str, Any] | None:
        bars = self._candles(symbol, 2, "1d")
        if not bars:
            return None
        last = bars[-1]
        spread_pct = 0.0005
        bid = round(last["close"] * (1 - spread_pct), 2)
        ask = round(last["close"] * (1 + spread_pct), 2)
        rng = np.random.default_rng(self._seed(symbol + "vol"))
        return {**last, "bid": bid, "ask": ask, "spread": round(ask - bid, 4),
                "volume_24h": round(float(rng.uniform(1e6, 5e7)), 2)}

    async def fetch_order_book(self, symbol: str, depth: int = 10) -> dict[str, Any] | None:
        ticker = await self.fetch_ticker(symbol)
        if not ticker:
            return None
        mid = ticker["close"]
        rng = np.random.default_rng(self._seed(symbol + "ob"))
        tick = mid * 0.0001
        bids = [[round(mid - tick * i * rng.uniform(1, 3), 2), round(float(rng.uniform(0.1, 10)), 4)]
                for i in range(1, depth + 1)]
        asks = [[round(mid + tick * i * rng.uniform(1, 3), 2), round(float(rng.uniform(0.1, 10)), 4)]
                for i in range(1, depth + 1)]
        return {
            "symbol": symbol,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "bids": bids, "asks": asks, "exchange": "demo",
        }
