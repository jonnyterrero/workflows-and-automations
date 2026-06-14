"""Reddit social provider — uses Reddit's public JSON search API (read-only)."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
import structlog
import xxhash

from packages.data_providers.base import BaseSocialProvider, ProviderConfig, ProviderError

logger = structlog.get_logger()

_DEFAULT_SUBREDDITS = ["investing", "wallstreetbets", "stocks", "CryptoCurrency", "StockMarket"]


class RedditSocialProvider(BaseSocialProvider):
    def __init__(self, subreddits: list[str] | None = None) -> None:
        env_subs = os.getenv("REDDIT_SUBREDDITS", "")
        if subreddits:
            subs = subreddits
        elif env_subs.strip():
            subs = [s.strip().lstrip("r/") for s in env_subs.split(",") if s.strip()]
        else:
            subs = _DEFAULT_SUBREDDITS

        self._subreddits = subs
        self._user_agent = os.getenv(
            "REDDIT_USER_AGENT",
            "trading-intelligence-agent/0.1 (by /u/trading_intel_bot)",
        )
        super().__init__(ProviderConfig(name="reddit", demo_mode=False))
        self._log = logger.bind(provider="reddit")

    def _author_hash(self, author: str) -> str:
        return xxhash.xxh64(author.encode()).hexdigest()[:16]

    async def _search_subreddit(
        self, subreddit: str, query: str, limit: int, hours_back: int,
    ) -> list[dict[str, Any]]:
        url = f"https://www.reddit.com/r/{subreddit}/search.json"
        params = {
            "q": query,
            "restrict_sr": "1",
            "sort": "new",
            "limit": str(min(limit, 25)),
            "t": "day" if hours_back <= 24 else "week",
        }
        headers = {"User-Agent": self._user_agent}

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            try:
                response = await client.get(url, params=params, headers=headers)
                if response.status_code == 429:
                    raise ProviderError("Reddit rate limit — slow down requests")
                response.raise_for_status()
                payload = response.json()
            except httpx.HTTPError as exc:
                raise ProviderError(f"Reddit request failed for r/{subreddit}: {exc}") from exc

        cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=hours_back)
        now = datetime.now(tz=timezone.utc).isoformat()
        posts: list[dict[str, Any]] = []

        for child in payload.get("data", {}).get("children", []):
            data = child.get("data", {})
            created = datetime.fromtimestamp(data.get("created_utc", 0), tz=timezone.utc)
            if created < cutoff:
                continue

            title = data.get("title", "")
            selftext = data.get("selftext", "")
            text = f"{title}\n{selftext}".strip()
            permalink = data.get("permalink", "")
            full_url = f"https://www.reddit.com{permalink}" if permalink else data.get("url", "")

            posts.append({
                "platform": "reddit",
                "source_community": f"r/{subreddit}",
                "author_hash": self._author_hash(data.get("author", "unknown")),
                "url": full_url,
                "posted_at": created.isoformat(),
                "fetched_at": now,
                "text": text,
                "tickers_mentioned": [],
                "assets_mentioned": [],
                "engagement_score": min(1.0, (data.get("score", 0) or 0) / 500),
                "credibility_score": 0.5,
                "sentiment_score": 0.0,
                "toxicity_or_spam_score": 0.1 if data.get("stickied") else 0.0,
            })
        return posts

    async def fetch_posts(
        self, query: str = "", subreddit_or_community: str = "",
        limit: int = 20, hours_back: int = 24,
    ) -> list[dict[str, Any]]:
        subs = [subreddit_or_community.lstrip("r/")] if subreddit_or_community else self._subreddits
        per_sub = max(3, limit // max(len(subs), 1))
        all_posts: list[dict[str, Any]] = []

        for sub in subs:
            try:
                batch = await self._search_subreddit(sub, query or "stock OR market", per_sub, hours_back)
                all_posts.extend(batch)
            except ProviderError as exc:
                self._log.warning("reddit_sub_failed", subreddit=sub, error=str(exc))

        all_posts.sort(key=lambda p: p["posted_at"], reverse=True)
        return all_posts[:limit]
