"""RSS news feed provider — public feeds from Reuters, Bloomberg, Yahoo, etc."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import feedparser
import httpx
import structlog
import xxhash

from packages.data_providers.base import BaseNewsProvider, ProviderConfig, ProviderError

logger = structlog.get_logger()

_DEFAULT_FEEDS: list[tuple[str, str]] = [
    ("Reuters Business", "https://feeds.reuters.com/reuters/businessNews"),
    ("Bloomberg Markets", "https://feeds.bloomberg.com/markets/news.rss"),
    ("Yahoo Finance", "https://finance.yahoo.com/news/rssindex"),
    ("MarketWatch Top Stories", "https://feeds.marketwatch.com/marketwatch/topstories/"),
    ("CNBC Finance", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664"),
]


def _content_hash(title: str, url: str) -> str:
    return xxhash.xxh64(f"{title}|{url}".encode()).hexdigest()


def _parse_published(entry: Any) -> datetime:
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        return datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
    published = getattr(entry, "published", "") or getattr(entry, "updated", "")
    if published:
        try:
            dt = parsedate_to_datetime(published)
            return dt.astimezone(timezone.utc)
        except (TypeError, ValueError, OverflowError):
            pass
    return datetime.now(tz=timezone.utc)


class RssNewsProvider(BaseNewsProvider):
    def __init__(self, feed_urls: list[str] | None = None) -> None:
        env_feeds = os.getenv("RSS_FEED_URLS", "")
        if feed_urls:
            feeds = [(f"RSS-{i}", url) for i, url in enumerate(feed_urls)]
        elif env_feeds.strip():
            urls = [u.strip() for u in env_feeds.split(",") if u.strip()]
            feeds = [(f"RSS-{i}", url) for i, url in enumerate(urls)]
        else:
            feeds = list(_DEFAULT_FEEDS)

        super().__init__(ProviderConfig(name="rss_news", demo_mode=False))
        self._feeds = feeds
        self._log = logger.bind(provider="rss_news")

    async def _fetch_feed(self, source_name: str, url: str) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            try:
                response = await client.get(
                    url,
                    headers={"User-Agent": "trading-intelligence-agent/0.1 (research feed reader)"},
                )
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise ProviderError(f"RSS fetch failed for {source_name}: {exc}") from exc

        parsed = feedparser.parse(response.text)
        now = datetime.now(tz=timezone.utc).isoformat()
        articles: list[dict[str, Any]] = []
        for entry in parsed.entries:
            title = (getattr(entry, "title", "") or "").strip()
            link = (getattr(entry, "link", "") or "").strip()
            if not title or not link:
                continue
            summary = getattr(entry, "summary", "") or getattr(entry, "description", "") or ""
            published_at = _parse_published(entry)
            articles.append({
                "source": source_name,
                "author": getattr(entry, "author", None),
                "title": title,
                "url": link,
                "published_at": published_at.isoformat(),
                "fetched_at": now,
                "summary": summary[:500] if summary else "",
                "content_hash": _content_hash(title, link),
                "tickers_mentioned": [],
                "assets_mentioned": [],
                "raw_text": summary,
                "credibility_score": 0.75 if "bloomberg" in source_name.lower() or "reuters" in source_name.lower() else 0.6,
            })
        return articles

    async def fetch_articles(
        self, query: str = "", limit: int = 20, hours_back: int = 24,
    ) -> list[dict[str, Any]]:
        cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=hours_back)
        q = query.upper().strip()
        all_articles: list[dict[str, Any]] = []

        for source_name, url in self._feeds:
            try:
                batch = await self._fetch_feed(source_name, url)
                all_articles.extend(batch)
            except ProviderError as exc:
                self._log.warning("rss_feed_failed", source=source_name, error=str(exc))

        filtered: list[dict[str, Any]] = []
        for article in all_articles:
            pub = datetime.fromisoformat(article["published_at"].replace("Z", "+00:00"))
            if pub < cutoff:
                continue
            if q:
                haystack = f"{article['title']} {article.get('summary', '')}".upper()
                if q not in haystack and q not in [t.upper() for t in article.get("tickers_mentioned", [])]:
                    continue
            filtered.append(article)

        filtered.sort(key=lambda a: a["published_at"], reverse=True)
        return filtered[:limit]
