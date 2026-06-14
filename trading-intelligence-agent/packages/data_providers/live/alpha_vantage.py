"""Alpha Vantage market data provider."""
from __future__ import annotations

import asyncio
import os
import time
from datetime import datetime, timezone
from typing import Any

import httpx
import structlog
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from packages.data_providers.base import (
    AuthError,
    BaseMarketDataProvider,
    ParseError,
    ProviderConfig,
    ProviderError,
    RateLimitConfig,
    RateLimitError,
)

logger = structlog.get_logger()

AV_BASE_URL = "https://www.alphavantage.co/query"
# Free tier: 5 requests/minute
_MIN_REQUEST_INTERVAL = 12.5


class _AlphaVantageRateLimiter:
    _lock = asyncio.Lock()
    _last_request_at = 0.0

    @classmethod
    async def wait(cls) -> None:
        async with cls._lock:
            now = time.monotonic()
            elapsed = now - cls._last_request_at
            if elapsed < _MIN_REQUEST_INTERVAL:
                await asyncio.sleep(_MIN_REQUEST_INTERVAL - elapsed)
            cls._last_request_at = time.monotonic()


class AlphaVantageMarketProvider(BaseMarketDataProvider):
    def __init__(self, api_key: str | None = None) -> None:
        key = api_key or os.getenv("ALPHA_VANTAGE_API_KEY", "")
        if not key:
            raise AuthError("ALPHA_VANTAGE_API_KEY is required for AlphaVantageMarketProvider")
        super().__init__(ProviderConfig(
            name="alpha_vantage",
            api_key=key,
            base_url=AV_BASE_URL,
            rate_limit=RateLimitConfig(requests_per_minute=5, retry_max_attempts=3),
            timeout_seconds=45.0,
            demo_mode=False,
        ))
        self._log = logger.bind(provider="alpha_vantage")

    def _is_crypto(self, symbol: str) -> bool:
        return "-USD" in symbol.upper() or symbol.upper() in {"BTC", "ETH"}

    def _parse_crypto_symbol(self, symbol: str) -> tuple[str, str]:
        upper = symbol.upper()
        if "-USD" in upper:
            base = upper.split("-")[0]
            return base, "USD"
        return upper, "USD"

    def _parse_equity_symbol(self, symbol: str) -> str:
        return symbol.upper().split("-")[0]

    @retry(
        retry=retry_if_exception_type(ProviderError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, max=60),
        reraise=True,
    )
    async def _request(self, params: dict[str, str]) -> dict[str, Any]:
        await _AlphaVantageRateLimiter.wait()
        params = {**params, "apikey": self.config.api_key or ""}

        async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
            try:
                response = await client.get(self.config.base_url, params=params)
            except httpx.RequestError as exc:
                raise ProviderError(f"Alpha Vantage request failed: {exc}") from exc

            if response.status_code == 429:
                raise RateLimitError("Alpha Vantage rate limit exceeded")
            if response.status_code != 200:
                raise ProviderError(f"Alpha Vantage HTTP {response.status_code}")

            try:
                payload = response.json()
            except ValueError as exc:
                raise ParseError("Alpha Vantage returned non-JSON response") from exc

        if "Error Message" in payload:
            raise ProviderError(payload["Error Message"])
        if "Note" in payload:
            raise RateLimitError(payload["Note"])
        if "Information" in payload:
            raise RateLimitError(payload["Information"])
        return payload

    def _parse_daily_bars(
        self, payload: dict[str, Any], symbol: str, interval: str,
        start: datetime | None, end: datetime | None,
    ) -> list[dict[str, Any]]:
        series_key = next(
            (k for k in payload if "Time Series" in k),
            None,
        )
        if not series_key:
            raise ParseError("Alpha Vantage response missing time series")

        bars: list[dict[str, Any]] = []
        for date_str, values in payload[series_key].items():
            ts = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            if start and ts < start:
                continue
            if end and ts > end:
                continue
            bars.append({
                "symbol": symbol,
                "timestamp": ts.isoformat(),
                "open": float(values.get("1. open", values.get("1a. open (USD)", 0))),
                "high": float(values.get("2. high", values.get("2a. high (USD)", 0))),
                "low": float(values.get("3. low", values.get("3a. low (USD)", 0))),
                "close": float(values.get("4. close", values.get("4a. close (USD)", 0))),
                "volume": int(float(values.get("5. volume", values.get("5. volume", 0)) or 0)),
                "source": "alpha_vantage",
                "interval": interval,
            })
        bars.sort(key=lambda b: b["timestamp"])
        return bars

    async def fetch_ohlcv(
        self, symbol: str, interval: str = "1d",
        start: datetime | None = None, end: datetime | None = None,
    ) -> list[dict[str, Any]]:
        if interval not in {"1d", "daily"}:
            self._log.warning("alpha_vantage_interval_fallback", interval=interval, using="1d")

        end = end or datetime.now(tz=timezone.utc)
        if self._is_crypto(symbol):
            base, market = self._parse_crypto_symbol(symbol)
            payload = await self._request({
                "function": "DIGITAL_CURRENCY_DAILY",
                "symbol": base,
                "market": market,
            })
            return self._parse_daily_bars(payload, symbol, "1d", start, end)

        equity = self._parse_equity_symbol(symbol)
        payload = await self._request({
            "function": "TIME_SERIES_DAILY",
            "symbol": equity,
            "outputsize": "compact",
        })
        return self._parse_daily_bars(payload, symbol, "1d", start, end)

    async def fetch_latest_quote(self, symbol: str) -> dict[str, Any] | None:
        if self._is_crypto(symbol):
            bars = await self.fetch_ohlcv(symbol, "1d")
            return bars[-1] if bars else None

        equity = self._parse_equity_symbol(symbol)
        payload = await self._request({"function": "GLOBAL_QUOTE", "symbol": equity})
        quote = payload.get("Global Quote", {})
        if not quote:
            return None

        price = float(quote.get("05. price", 0) or 0)
        if price == 0:
            return None

        ts_raw = quote.get("07. latest trading day", "")
        ts = (
            datetime.strptime(ts_raw, "%Y-%m-%d").replace(tzinfo=timezone.utc).isoformat()
            if ts_raw else datetime.now(tz=timezone.utc).isoformat()
        )
        return {
            "symbol": symbol,
            "timestamp": ts,
            "open": float(quote.get("02. open", price) or price),
            "high": float(quote.get("03. high", price) or price),
            "low": float(quote.get("04. low", price) or price),
            "close": price,
            "volume": int(float(quote.get("06. volume", 0) or 0)),
            "source": "alpha_vantage",
            "interval": "1d",
        }
