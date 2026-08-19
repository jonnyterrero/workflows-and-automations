"""Alpha Vantage crypto provider — live OHLCV and tickers for digital assets."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import structlog

from packages.data_providers.base import AuthError, BaseCryptoProvider, ProviderConfig, RateLimitConfig
from packages.data_providers.live.alpha_vantage import AlphaVantageMarketProvider

logger = structlog.get_logger()

# Symbols Alpha Vantage supports well on the free tier
SUPPORTED_CRYPTO = {"BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "DOGE-USD", "ADA-USD"}


class AlphaVantageCryptoProvider(BaseCryptoProvider):
    """Live crypto prices via Alpha Vantage DIGITAL_CURRENCY_DAILY."""

    def __init__(self, api_key: str | None = None) -> None:
        key = api_key or os.getenv("ALPHA_VANTAGE_API_KEY", "")
        if not key:
            raise AuthError("ALPHA_VANTAGE_API_KEY is required for AlphaVantageCryptoProvider")
        super().__init__(ProviderConfig(
            name="alpha_vantage_crypto",
            api_key=key,
            rate_limit=RateLimitConfig(requests_per_minute=5, retry_max_attempts=3),
            timeout_seconds=45.0,
            demo_mode=False,
        ))
        self._av = AlphaVantageMarketProvider(api_key=key)
        self._log = logger.bind(provider="alpha_vantage_crypto")

    async def fetch_ohlcv(
        self, symbol: str, interval: str = "1d", limit: int = 60,
    ) -> list[dict[str, Any]]:
        end = datetime.now(tz=timezone.utc)
        start = end - timedelta(days=max(limit, 30))
        bars = await self._av.fetch_ohlcv(symbol, interval, start, end)
        normalized = [{**b, "source": "alpha_vantage_crypto"} for b in bars]
        return normalized[-limit:]

    async def fetch_ticker(self, symbol: str) -> dict[str, Any] | None:
        quote = await self._av.fetch_latest_quote(symbol)
        if not quote:
            return None
        close = float(quote.get("close", 0) or 0)
        spread_pct = 0.001
        return {
            **quote,
            "source": "alpha_vantage_crypto",
            "bid": round(close * (1 - spread_pct), 4),
            "ask": round(close * (1 + spread_pct), 4),
            "spread": round(close * spread_pct * 2, 4),
            "volume_24h": float(quote.get("volume", 0) or 0),
        }

    async def fetch_order_book(self, symbol: str, depth: int = 10) -> dict[str, Any] | None:
        # Alpha Vantage free tier has no order book endpoint — return None in live mode.
        self._log.debug("order_book_unavailable", symbol=symbol, reason="not_supported_by_provider")
        return None
