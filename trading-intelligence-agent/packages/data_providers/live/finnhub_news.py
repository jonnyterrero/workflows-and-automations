"""Finnhub company and market news provider."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
import structlog
import xxhash

from packages.data_providers.base import (
    AuthError,
    BaseNewsProvider,
    ProviderConfig,
    ProviderError,
    RateLimitConfig,
    RateLimitError,
)

logger = structlog.get_logger()

FINNHUB_BASE_URL = "https://finnhub.io/api/v1"


def _content_hash(title: str, url: str) -> str:
    return xxhash.xxh64(f"{title}|{url}".encode()).hexdigest()


class FinnhubNewsProvider(BaseNewsProvider):
    """Finnhub news for symbols, general market categories, and crypto headlines."""

    def __init__(self, api_key: str | None = None) -> None:
        key = api_key or os.getenv("FINNHUB_API_KEY", "")
        if not key:
            raise AuthError("FINNHUB_API_KEY is required for FinnhubNewsProvider")
        super().__init__(ProviderConfig(
            name="finnhub_news",
            api_key=key,
            base_url=FINNHUB_BASE_URL,
            rate_limit=RateLimitConfig(requests_per_minute=60, retry_max_attempts=3),
            timeout_seconds=30.0,
            demo_mode=False,
        ))
        self._log = logger.bind(provider="finnhub_news")

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

    def _normalize_articles(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        now = datetime.now(tz=timezone.utc).isoformat()
        articles: list[dict[str, Any]] = []
        for item in items:
            title = str(item.get("headline") or item.get("title") or "").strip()
            url = str(item.get("url") or item.get("link") or "").strip()
            if not title or not url:
                continue
            ts = item.get("datetime") or item.get("time")
            if isinstance(ts, (int, float)):
                published_at = datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat()
            else:
                published_at = now
            source_name = str(item.get("source") or "Finnhub")
            summary = str(item.get("summary") or "").strip()
            credibility = 0.78 if source_name.lower() in {"reuters", "bloomberg", "marketwatch"} else 0.68
            articles.append({
                "source": source_name,
                "author": None,
                "title": title,
                "url": url,
                "published_at": published_at,
                "fetched_at": now,
                "summary": summary[:500],
                "content_hash": _content_hash(title, url),
                "tickers_mentioned": [],
                "assets_mentioned": [],
                "raw_text": summary,
                "credibility_score": credibility,
            })
        return articles

    def _is_symbol_query(self, query: str) -> bool:
        stripped = query.strip().upper()
        if not stripped or " " in stripped:
            return False
        return all(ch.isalnum() or ch in {"-", ".", "$"} for ch in stripped)

    async def fetch_articles(
        self,
        query: str = "",
        limit: int = 20,
        hours_back: int = 24,
    ) -> list[dict[str, Any]]:
        q = query.strip()
        if self._is_symbol_query(q):
            end = datetime.now(tz=timezone.utc).date()
            start = end - timedelta(days=max(1, int(hours_back / 24) + 2))
            items = await self._get(
                "/company-news",
                params={
                    "symbol": q.upper().split("-")[0],
                    "from": start.isoformat(),
                    "to": end.isoformat(),
                },
            )
            return self._normalize_articles(items)[:limit]

        items = await self._get("/news", params={"category": "general"})
        articles = self._normalize_articles(items)
        if q:
            upper = q.upper()
            articles = [
                art for art in articles
                if upper in f"{art['title']} {art.get('summary', '')}".upper()
            ]
        return articles[:limit]

    async def fetch_crypto_articles(self, limit: int = 20, hours_back: int = 48) -> list[dict[str, Any]]:
        items = await self._get("/news", params={"category": "crypto"})
        return self._normalize_articles(items)[:limit]
