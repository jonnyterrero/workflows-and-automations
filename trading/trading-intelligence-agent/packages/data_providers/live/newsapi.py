"""NewsAPI.org provider — free developer tier (100 req/day, non-commercial)."""
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

NEWSAPI_BASE = "https://newsapi.org/v2"


def _content_hash(title: str, url: str) -> str:
    return xxhash.xxh64(f"{title}|{url}".encode()).hexdigest()


class NewsApiProvider(BaseNewsProvider):
    """NewsAPI free tier — conservative call budget for personal/non-commercial use."""

    def __init__(self, api_key: str | None = None) -> None:
        key = api_key or os.getenv("NEWSAPI_KEY", "")
        if not key:
            raise AuthError("NEWSAPI_KEY is required for NewsApiProvider")
        self._max_calls = int(os.getenv("NEWSAPI_MAX_CALLS_PER_RUN", "3"))
        self._calls_this_run = 0
        super().__init__(ProviderConfig(
            name="newsapi",
            api_key=key,
            base_url=NEWSAPI_BASE,
            rate_limit=RateLimitConfig(requests_per_day=100, requests_per_minute=10),
            timeout_seconds=30.0,
            demo_mode=False,
        ))
        self._log = logger.bind(provider="newsapi")

    def _can_call(self) -> bool:
        return self._calls_this_run < self._max_calls

    async def _everything(
        self, query: str, limit: int, hours_back: int,
    ) -> list[dict[str, Any]]:
        if not self._can_call():
            self._log.warning("newsapi_budget_exhausted", max_calls=self._max_calls)
            return []

        from_dt = (datetime.now(tz=timezone.utc) - timedelta(hours=hours_back)).strftime("%Y-%m-%dT%H:%M:%S")
        params = {
            "q": query,
            "from": from_dt,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": str(min(limit, 20)),
            "apiKey": self.config.api_key or "",
        }

        async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
            try:
                response = await client.get(f"{self.config.base_url}/everything", params=params)
            except httpx.RequestError as exc:
                raise ProviderError(f"NewsAPI request failed: {exc}") from exc

            self._calls_this_run += 1

            if response.status_code == 401:
                raise AuthError("NewsAPI key invalid")
            if response.status_code == 429:
                raise RateLimitError("NewsAPI daily/monthly limit reached")
            if response.status_code != 200:
                raise ProviderError(f"NewsAPI HTTP {response.status_code}: {response.text[:200]}")

            payload = response.json()

        if payload.get("status") != "ok":
            raise ProviderError(payload.get("message", "NewsAPI error"))

        now = datetime.now(tz=timezone.utc).isoformat()
        articles: list[dict[str, Any]] = []
        for item in payload.get("articles", []):
            title = (item.get("title") or "").strip()
            url = (item.get("url") or "").strip()
            if not title or not url or title == "[Removed]":
                continue
            source_name = (item.get("source") or {}).get("name", "NewsAPI")
            published = item.get("publishedAt", now)
            description = item.get("description") or item.get("content") or ""
            credibility = 0.8 if any(
                k in source_name.lower() for k in ("bloomberg", "reuters", "wall street", "financial times")
            ) else 0.65
            articles.append({
                "source": source_name,
                "author": item.get("author"),
                "title": title,
                "url": url,
                "published_at": published,
                "fetched_at": now,
                "summary": description[:500] if description else "",
                "content_hash": _content_hash(title, url),
                "tickers_mentioned": [],
                "assets_mentioned": [],
                "raw_text": description,
                "credibility_score": credibility,
            })
        return articles

    async def fetch_articles(
        self, query: str = "", limit: int = 20, hours_back: int = 24,
    ) -> list[dict[str, Any]]:
        q = query.strip()
        if not q:
            q = "stock market OR federal reserve OR earnings"
        return await self._everything(q, limit, hours_back)

    async def fetch_crypto_articles(self, limit: int = 15, hours_back: int = 48) -> list[dict[str, Any]]:
        return await self._everything(
            "bitcoin OR ethereum OR cryptocurrency OR crypto ETF OR blockchain",
            limit,
            hours_back,
        )
