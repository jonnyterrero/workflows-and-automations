"""Polygon/Massive market data provider for equities and ETFs."""
from __future__ import annotations

import os
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

POLYGON_BASE_URL = "https://api.polygon.io"


class PolygonMarketProvider(BaseMarketDataProvider):
    """Live equity and ETF OHLCV/quote data via Polygon/Massive REST."""

    def __init__(self, api_key: str | None = None) -> None:
        key = api_key or os.getenv("POLYGON_API_KEY", "")
        if not key:
            raise AuthError("POLYGON_API_KEY is required for PolygonMarketProvider")
        super().__init__(ProviderConfig(
            name="polygon",
            api_key=key,
            base_url=POLYGON_BASE_URL,
            rate_limit=RateLimitConfig(requests_per_minute=60, retry_max_attempts=3),
            timeout_seconds=30.0,
            demo_mode=False,
        ))
        self._log = logger.bind(provider="polygon")

    def _symbol(self, symbol: str) -> str:
        return symbol.upper().split("-")[0]

    @retry(
        retry=retry_if_exception_type(ProviderError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, max=30),
        reraise=True,
    )
    async def _request(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        query = dict(params or {})
        query["apiKey"] = self.config.api_key or ""
        async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
            try:
                response = await client.get(f"{self.config.base_url}{path}", params=query)
            except httpx.RequestError as exc:
                raise ProviderError(f"Polygon request failed: {exc}") from exc

        if response.status_code == 401:
            raise AuthError("Polygon API key invalid")
        if response.status_code == 429:
            raise RateLimitError("Polygon rate limit exceeded")
        if response.status_code >= 400:
            raise ProviderError(f"Polygon HTTP {response.status_code}: {response.text[:200]}")

        try:
            payload = response.json()
        except ValueError as exc:
            raise ParseError("Polygon returned non-JSON response") from exc

        if payload.get("status") == "ERROR":
            msg = payload.get("error") or payload.get("message") or "Polygon error"
            if "rate" in msg.lower():
                raise RateLimitError(msg)
            raise ProviderError(msg)
        return payload

    async def fetch_ohlcv(
        self,
        symbol: str,
        interval: str = "1d",
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[dict[str, Any]]:
        ticker = self._symbol(symbol)
        from_date = (start or datetime.now(tz=timezone.utc)).date().isoformat()
        to_date = (end or datetime.now(tz=timezone.utc)).date().isoformat()
        payload = await self._request(
            f"/v2/aggs/ticker/{ticker}/range/1/day/{from_date}/{to_date}",
            params={"adjusted": "true", "sort": "asc", "limit": 5000},
        )
        results = payload.get("results")
        if results is None:
            raise ParseError("Polygon aggregate response missing results")

        bars: list[dict[str, Any]] = []
        for item in results:
            ts_ms = int(item.get("t", 0) or 0)
            if not ts_ms:
                continue
            ts = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
            bars.append({
                "symbol": symbol.upper(),
                "timestamp": ts.isoformat(),
                "open": float(item.get("o", 0) or 0),
                "high": float(item.get("h", 0) or 0),
                "low": float(item.get("l", 0) or 0),
                "close": float(item.get("c", 0) or 0),
                "adjusted_close": float(item.get("c", 0) or 0),
                "volume": float(item.get("v", 0) or 0),
                "source": "polygon",
                "interval": "1d",
            })
        return bars

    async def fetch_latest_quote(self, symbol: str) -> dict[str, Any] | None:
        ticker = self._symbol(symbol)
        today = datetime.now(tz=timezone.utc).date().isoformat()

        try:
            payload = await self._request(
                f"/v1/open-close/{ticker}/{today}",
                params={"adjusted": "true"},
            )
            ts = payload.get("from") or today
            if payload.get("close") is not None:
                return {
                    "symbol": symbol.upper(),
                    "timestamp": f"{ts}T00:00:00+00:00" if len(str(ts)) == 10 else str(ts),
                    "open": float(payload.get("open", payload.get("close", 0)) or 0),
                    "high": float(payload.get("high", payload.get("close", 0)) or 0),
                    "low": float(payload.get("low", payload.get("close", 0)) or 0),
                    "close": float(payload.get("close", 0) or 0),
                    "adjusted_close": float(payload.get("close", 0) or 0),
                    "volume": float(payload.get("volume", 0) or 0),
                    "source": "polygon",
                    "interval": "1d",
                }
        except ProviderError as exc:
            self._log.warning("polygon_open_close_failed", symbol=ticker, error=str(exc))

        payload = await self._request(
            f"/v2/aggs/ticker/{ticker}/prev",
            params={"adjusted": "true"},
        )
        results = payload.get("results") or []
        if not results:
            return None
        item = results[0]
        ts = datetime.fromtimestamp(int(item.get("t", 0)) / 1000, tz=timezone.utc)
        return {
            "symbol": symbol.upper(),
            "timestamp": ts.isoformat(),
            "open": float(item.get("o", 0) or 0),
            "high": float(item.get("h", 0) or 0),
            "low": float(item.get("l", 0) or 0),
            "close": float(item.get("c", 0) or 0),
            "adjusted_close": float(item.get("c", 0) or 0),
            "volume": float(item.get("v", 0) or 0),
            "source": "polygon",
            "interval": "1d",
        }
