"""FRED (Federal Reserve Economic Data) macro provider."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import httpx
import structlog
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from packages.data_providers.base import (
    AuthError,
    BaseMacroProvider,
    ParseError,
    ProviderConfig,
    ProviderError,
    RateLimitConfig,
    RateLimitError,
)

logger = structlog.get_logger()

FRED_BASE_URL = "https://api.stlouisfed.org/fred"

# Internal series_id -> FRED series + metadata
_SERIES_MAP: dict[str, dict[str, str]] = {
    "fed_funds_rate": {"fred_id": "FEDFUNDS", "category": "monetary_policy", "unit": "percent"},
    "cpi_yoy": {"fred_id": "CPIAUCSL", "category": "inflation", "unit": "percent", "yoy": "true"},
    "gdp_growth_qoq": {"fred_id": "A191RL1Q225SBEA", "category": "growth", "unit": "percent"},
    "unemployment_rate": {"fred_id": "UNRATE", "category": "labor", "unit": "percent"},
    "10y_treasury_yield": {"fred_id": "DGS10", "category": "rates", "unit": "percent"},
    "2y_treasury_yield": {"fred_id": "DGS2", "category": "rates", "unit": "percent"},
    "vix": {"fred_id": "VIXCLS", "category": "volatility", "unit": "index"},
    "dxy": {"fred_id": "DTWEXBGS", "category": "forex", "unit": "index"},
}

_YIELD_CURVE: dict[str, str] = {
    "3m": "DGS3MO",
    "6m": "DGS6MO",
    "1y": "DGS1",
    "2y": "DGS2",
    "5y": "DGS5",
    "10y": "DGS10",
    "30y": "DGS30",
}


class FredMacroProvider(BaseMacroProvider):
    def __init__(self, api_key: str | None = None) -> None:
        key = api_key or os.getenv("FRED_API_KEY", "")
        if not key:
            raise AuthError("FRED_API_KEY is required for FredMacroProvider")
        super().__init__(ProviderConfig(
            name="fred",
            api_key=key,
            base_url=FRED_BASE_URL,
            rate_limit=RateLimitConfig(requests_per_minute=120, retry_max_attempts=3),
            timeout_seconds=30.0,
            demo_mode=False,
        ))
        self._log = logger.bind(provider="fred")

    @retry(
        retry=retry_if_exception_type(ProviderError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, max=30),
        reraise=True,
    )
    async def _fetch_observations(self, fred_id: str, limit: int) -> list[dict[str, str]]:
        params = {
            "series_id": fred_id,
            "api_key": self.config.api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": limit,
        }
        url = f"{self.config.base_url}/series/observations"
        async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
            try:
                response = await client.get(url, params=params)
            except httpx.RequestError as exc:
                raise ProviderError(f"FRED request failed: {exc}") from exc

            if response.status_code == 429:
                raise RateLimitError("FRED rate limit exceeded")
            if response.status_code in (401, 403):
                raise AuthError("FRED API key invalid or unauthorized")
            if response.status_code != 200:
                raise ProviderError(f"FRED HTTP {response.status_code}")

            try:
                payload = response.json()
            except ValueError as exc:
                raise ParseError("FRED returned non-JSON response") from exc

        observations = payload.get("observations", [])
        if not observations:
            return []
        return list(reversed(observations))

    def _compute_cpi_yoy(self, observations: list[dict[str, str]]) -> list[dict[str, Any]]:
        """Convert monthly CPI index levels to YoY percent change."""
        valid = [
            (obs["date"], float(obs["value"]))
            for obs in observations
            if obs.get("value") not in (None, ".", "")
        ]
        if len(valid) < 13:
            return []

        now = datetime.now(tz=timezone.utc).isoformat()
        results: list[dict[str, Any]] = []
        for i in range(12, len(valid)):
            date_str, current = valid[i]
            _, prior = valid[i - 12]
            if prior == 0:
                continue
            yoy = round((current - prior) / prior * 100, 2)
            results.append({
                "series_id": "cpi_yoy",
                "value": yoy,
                "observation_date": f"{date_str}T00:00:00+00:00",
                "category": "inflation",
                "unit": "percent",
                "source": "fred",
                "fetched_at": now,
            })
        return results[-12:]

    async def fetch_indicator(self, series_id: str, limit: int = 12) -> list[dict[str, Any]]:
        spec = _SERIES_MAP.get(series_id)
        if not spec:
            self._log.warning("fred_unknown_series", series_id=series_id)
            return []

        fred_id = spec["fred_id"]
        fetch_limit = max(limit + 13, 25) if spec.get("yoy") == "true" else limit
        observations = await self._fetch_observations(fred_id, fetch_limit)
        now = datetime.now(tz=timezone.utc).isoformat()

        if spec.get("yoy") == "true":
            return self._compute_cpi_yoy(observations)[-limit:]

        results: list[dict[str, Any]] = []
        for obs in observations[-limit:]:
            value_raw = obs.get("value", "")
            if value_raw in (None, ".", ""):
                continue
            date_str = obs.get("date", "")
            results.append({
                "series_id": series_id,
                "value": float(value_raw),
                "observation_date": f"{date_str}T00:00:00+00:00",
                "category": spec["category"],
                "unit": spec["unit"],
                "source": "fred",
                "fetched_at": now,
            })
        return results

    async def fetch_yield_curve(self) -> list[dict[str, Any]]:
        now = datetime.now(tz=timezone.utc).isoformat()
        curve: list[dict[str, Any]] = []
        for maturity, fred_id in _YIELD_CURVE.items():
            try:
                observations = await self._fetch_observations(fred_id, limit=5)
            except ProviderError as exc:
                self._log.warning("yield_curve_point_failed", maturity=maturity, error=str(exc))
                continue

            latest = None
            for obs in reversed(observations):
                value_raw = obs.get("value", "")
                if value_raw not in (None, ".", ""):
                    latest = obs
                    break
            if not latest:
                continue

            curve.append({
                "maturity": maturity,
                "yield_pct": float(latest["value"]),
                "observation_date": f"{latest['date']}T00:00:00+00:00",
                "source": "fred",
                "fetched_at": now,
            })
        return curve
