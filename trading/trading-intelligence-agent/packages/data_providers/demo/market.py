"""Demo market data provider — returns synthetic OHLCV fixture data."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np
import structlog

from packages.data_providers.base import BaseMarketDataProvider, ProviderConfig

logger = structlog.get_logger()

_BASE_PRICES: dict[str, float] = {
    "SPY": 500.0, "QQQ": 430.0, "AAPL": 190.0, "NVDA": 880.0,
    "TSLA": 250.0, "TLT": 95.0, "BTC-USD": 67000.0, "ETH-USD": 3400.0,
}
_DEFAULT_BASE = 100.0
_MU = 0.0002
_SIGMA = 0.015


def _bdays_back(n: int, reference: datetime) -> list[datetime]:
    days: list[datetime] = []
    current = reference.replace(hour=0, minute=0, second=0, microsecond=0)
    while len(days) < n:
        if current.weekday() < 5:
            days.append(current)
        current -= timedelta(days=1)
    return list(reversed(days))


class DemoMarketDataProvider(BaseMarketDataProvider):
    def __init__(self) -> None:
        super().__init__(ProviderConfig(name="demo_market", demo_mode=True))

    def _seed(self, symbol: str) -> int:
        return abs(hash(symbol)) % (2**31)

    def _generate(self, symbol: str, n: int, interval: str, ref: datetime) -> list[dict[str, Any]]:
        rng = np.random.default_rng(self._seed(symbol))
        base = _BASE_PRICES.get(symbol.upper(), _DEFAULT_BASE)
        returns = rng.normal(_MU, _SIGMA, n)
        timestamps = _bdays_back(n, ref)
        bars: list[dict[str, Any]] = []
        close = base
        for i, ts in enumerate(timestamps):
            open_p = close
            close = round(open_p * (1 + returns[i]), 4)
            high = round(max(open_p, close) * (1 + abs(rng.normal(0, 0.003))), 4)
            low = round(min(open_p, close) * (1 - abs(rng.normal(0, 0.003))), 4)
            volume = int(rng.integers(500_000, 10_000_000))
            bars.append({
                "symbol": symbol, "timestamp": ts.isoformat(),
                "open": round(open_p, 4), "high": high, "low": low,
                "close": close, "volume": volume,
                "source": "demo", "interval": interval,
            })
        return bars

    async def fetch_ohlcv(
        self, symbol: str, interval: str = "1d",
        start: datetime | None = None, end: datetime | None = None,
    ) -> list[dict[str, Any]]:
        end = end or datetime.now(tz=timezone.utc)
        n = max(1, (end - start).days) if start else 60
        return self._generate(symbol, n, interval, end)

    async def fetch_latest_quote(self, symbol: str) -> dict[str, Any] | None:
        bars = self._generate(symbol, 2, "1d", datetime.now(tz=timezone.utc))
        return bars[-1] if bars else None

    async def fetch_batch_ohlcv(
        self, symbols: list[str], interval: str = "1d",
        start: datetime | None = None, end: datetime | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        return {s: await self.fetch_ohlcv(s, interval, start, end) for s in symbols}
