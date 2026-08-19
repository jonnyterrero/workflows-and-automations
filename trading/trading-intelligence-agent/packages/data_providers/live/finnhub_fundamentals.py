"""Finnhub fundamentals, earnings, and IPO calendar provider."""
from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone
from typing import Any

import httpx
import structlog

from packages.data_providers.base import (
    AuthError,
    BaseFundamentalsProvider,
    ProviderConfig,
    ProviderError,
    RateLimitConfig,
    RateLimitError,
)

logger = structlog.get_logger()

FINNHUB_BASE_URL = "https://finnhub.io/api/v1"


class FinnhubFundamentalsProvider(BaseFundamentalsProvider):
    """Fundamentals, earnings calendar, and IPO calendar via Finnhub."""

    def __init__(self, api_key: str | None = None) -> None:
        key = api_key or os.getenv("FINNHUB_API_KEY", "")
        if not key:
            raise AuthError("FINNHUB_API_KEY is required for FinnhubFundamentalsProvider")
        super().__init__(ProviderConfig(
            name="finnhub_fundamentals",
            api_key=key,
            base_url=FINNHUB_BASE_URL,
            rate_limit=RateLimitConfig(requests_per_minute=60, retry_max_attempts=3),
            timeout_seconds=30.0,
            demo_mode=False,
        ))
        self._log = logger.bind(provider="finnhub_fundamentals")

    async def _get(self, path: str, params: dict[str, Any]) -> Any:
        async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
            try:
                response = await client.get(
                    f"{self.config.base_url}{path}",
                    params=params,
                    headers={
                        "X-Finnhub-Token": self.config.api_key or "",
                        "User-Agent": "trading-intelligence-agent/0.1",
                    },
                )
            except httpx.RequestError as exc:
                raise ProviderError(f"Finnhub request failed: {exc}") from exc

        if response.status_code == 401:
            raise AuthError("Finnhub API key invalid")
        if response.status_code == 429:
            raise RateLimitError("Finnhub rate limit exceeded")
        if response.status_code >= 400:
            raise ProviderError(f"Finnhub HTTP {response.status_code}: {response.text[:200]}")
        return response.json()

    async def fetch_overview(self, symbol: str) -> dict[str, Any] | None:
        payload = await self._get(
            "/stock/metric",
            params={"symbol": symbol.upper().split("-")[0], "metric": "all"},
        )
        metrics = payload.get("metric") or {}
        if not metrics:
            return None
        return {
            "symbol": symbol.upper(),
            "source": "finnhub_fundamentals",
            "metric_type": payload.get("metricType"),
            "metrics": metrics,
            "series": payload.get("series") or {},
        }

    async def fetch_earnings(self, symbol: str) -> list[dict[str, Any]]:
        base_symbol = symbol.upper().split("-")[0]
        start = (date.today() - timedelta(days=45)).isoformat()
        end = (date.today() + timedelta(days=120)).isoformat()
        payload = await self._get(
            "/calendar/earnings",
            params={"from": start, "to": end, "symbol": base_symbol},
        )
        calendar = payload.get("earningsCalendar") or []
        events: list[dict[str, Any]] = []
        for item in calendar:
            events.append({
                "symbol": base_symbol,
                "date": item.get("date"),
                "hour": item.get("hour"),
                "eps_actual": item.get("epsActual"),
                "eps_estimate": item.get("epsEstimate"),
                "revenue_actual": item.get("revenueActual"),
                "revenue_estimate": item.get("revenueEstimate"),
                "quarter": item.get("quarter"),
                "year": item.get("year"),
                "source": "finnhub_fundamentals",
            })
        return events

    async def fetch_ipo_calendar(
        self,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[dict[str, Any]]:
        start = from_date or date.today()
        end = to_date or (start + timedelta(days=60))
        payload = await self._get(
            "/calendar/ipo",
            params={"from": start.isoformat(), "to": end.isoformat()},
        )
        calendar = payload.get("ipoCalendar") or []
        ipos: list[dict[str, Any]] = []
        fetched_at = datetime.now(tz=timezone.utc).isoformat()
        for item in calendar:
            ipos.append({
                "date": item.get("date"),
                "name": item.get("name"),
                "symbol": item.get("symbol"),
                "exchange": item.get("exchange"),
                "number_of_shares": item.get("numberOfShares"),
                "price": item.get("price"),
                "status": item.get("status"),
                "total_shares_value": item.get("totalSharesValue"),
                "fetched_at": fetched_at,
                "source": "finnhub_fundamentals",
            })
        return ipos
