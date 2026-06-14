"""X (Twitter) social provider — requires official API bearer token."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
import structlog
import xxhash

from packages.data_providers.base import (
    AuthError,
    BaseSocialProvider,
    ProviderConfig,
    ProviderError,
)
from packages.data_providers.live.x_setup import build_crypto_search_query, build_equity_search_query

logger = structlog.get_logger()

X_API_BASE = "https://api.twitter.com/2"


class XSocialProvider(BaseSocialProvider):
    """Fetches recent posts via X API v2 recent search.

    Requires X_BEARER_TOKEN in environment. Without it, returns empty results
    and logs a warning — no scraping of gated content.
    """

    def __init__(self, bearer_token: str | None = None) -> None:
        token = bearer_token or os.getenv("X_BEARER_TOKEN", "")
        super().__init__(ProviderConfig(
            name="x_twitter",
            api_key=token or None,
            base_url=X_API_BASE,
            demo_mode=False,
        ))
        self._bearer = token
        self._log = logger.bind(provider="x_twitter")

    def _author_hash(self, author_id: str) -> str:
        return xxhash.xxh64(author_id.encode()).hexdigest()[:16]

    def _build_query(self, query: str) -> str:
        if not query:
            return os.getenv(
                "X_DEFAULT_SEARCH_QUERY",
                "($SPY OR $NVDA OR $AAPL OR bitcoin OR $BTC OR ethereum) -is:retweet lang:en",
            )
        upper = query.upper()
        if "-USD" in upper or upper in {"BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "ADA"}:
            return build_crypto_search_query(query)
        return build_equity_search_query(query)

    async def fetch_posts(
        self, query: str = "", subreddit_or_community: str = "",
        limit: int = 20, hours_back: int = 24,
    ) -> list[dict[str, Any]]:
        if not self._bearer:
            self._log.warning("x_bearer_missing", hint="Set X_BEARER_TOKEN — see GET /admin/setup/x")
            return []

        search_query = self._build_query(query)
        start_time = (datetime.now(tz=timezone.utc) - timedelta(hours=hours_back)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

        params = {
            "query": search_query,
            "max_results": str(min(max(limit, 10), 100)),
            "start_time": start_time,
            "tweet.fields": "created_at,public_metrics,author_id",
        }
        headers = {"Authorization": f"Bearer {self._bearer}"}

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.config.base_url}/tweets/search/recent",
                    params=params,
                    headers=headers,
                )
                if response.status_code in (401, 403):
                    raise AuthError("X API bearer token invalid or unauthorized")
                if response.status_code == 429:
                    raise ProviderError("X API rate limit exceeded")
                response.raise_for_status()
                payload = response.json()
            except httpx.HTTPError as exc:
                raise ProviderError(f"X API request failed: {exc}") from exc

        now = datetime.now(tz=timezone.utc).isoformat()
        posts: list[dict[str, Any]] = []
        for tweet in payload.get("data", []):
            metrics = tweet.get("public_metrics", {})
            created_raw = tweet.get("created_at", now)
            posts.append({
                "platform": "x",
                "source_community": "x_search",
                "author_hash": self._author_hash(tweet.get("author_id", "unknown")),
                "url": f"https://x.com/i/web/status/{tweet.get('id', '')}",
                "posted_at": created_raw,
                "fetched_at": now,
                "text": tweet.get("text", ""),
                "tickers_mentioned": [],
                "assets_mentioned": [],
                "engagement_score": min(1.0, (metrics.get("like_count", 0) or 0) / 1000),
                "credibility_score": 0.45,
                "sentiment_score": 0.0,
                "toxicity_or_spam_score": 0.05,
            })
        return posts[:limit]
