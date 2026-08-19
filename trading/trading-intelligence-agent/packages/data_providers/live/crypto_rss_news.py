"""Crypto-focused RSS news — curated catalog with reliability-weighted credibility."""
from __future__ import annotations

import os
from typing import Any

from packages.data_providers.live.crypto_feeds_catalog import CryptoFeedEntry, load_crypto_rss_catalog
from packages.data_providers.live.rss_news import RssNewsProvider

# Fallback if YAML missing
_FALLBACK_FEEDS: list[tuple[str, str, int, str]] = [
    ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/", 8, "breaking_news"),
    ("The Block", "https://www.theblock.co/rss.xml", 9, "breaking_news"),
    ("Bloomberg Crypto", "https://feeds.bloomberg.com/crypto/news.rss", 10, "breaking_news"),
    ("Cointelegraph", "https://cointelegraph.com/rss", 7, "breaking_news"),
    ("Decrypt", "https://decrypt.co/feed", 7, "breaking_news"),
]


class CryptoRssNewsProvider(RssNewsProvider):
    """RSS provider scoped to verified crypto news outlets from crypto_rss_feeds.yaml."""

    def __init__(self, feed_urls: list[str] | None = None) -> None:
        self._feed_meta: dict[str, CryptoFeedEntry] = {}
        env_feeds = os.getenv("CRYPTO_RSS_FEED_URLS", "").strip()

        if feed_urls:
            feeds = [
                (url.split("/")[2] if "/" in url else f"Crypto-{i}", url)
                for i, url in enumerate(feed_urls)
            ]
        elif env_feeds:
            urls = [u.strip() for u in env_feeds.split(",") if u.strip()]
            feeds = [(u.split("/")[2] if "/" in u else f"Crypto-{i}", u) for i, u in enumerate(urls)]
        else:
            catalog = load_crypto_rss_catalog()
            if catalog:
                feeds = [(e.name, e.url) for e in catalog]
                self._feed_meta = {e.name: e for e in catalog}
            else:
                feeds = [(n, u) for n, u, _, _ in _FALLBACK_FEEDS]

        super().__init__(feed_urls=[url for _, url in feeds])
        self._feeds = feeds
        self.config.name = "crypto_rss_news"

    def _enrich_article(self, article: dict[str, Any], source_name: str) -> dict[str, Any]:
        meta = self._feed_meta.get(source_name)
        if meta:
            article["credibility_score"] = meta.credibility_score
            article["source_category"] = meta.category
            article["source_reliability"] = meta.reliability
            article["monitor_tier"] = meta.monitor
        else:
            src = source_name.lower()
            if any(k in src for k in ("bloomberg", "reuters", "sec", "cftc", "ethereum")):
                article["credibility_score"] = 0.85
            elif any(k in src for k in ("coindesk", "block", "immunefi")):
                article["credibility_score"] = 0.8
            else:
                article["credibility_score"] = max(article.get("credibility_score", 0.6), 0.65)
        article["asset_class"] = "crypto"
        return article

    async def fetch_articles(
        self, query: str = "", limit: int = 20, hours_back: int = 48,
    ) -> list[dict[str, Any]]:
        articles = await super().fetch_articles(query=query, limit=limit * 2, hours_back=hours_back)
        enriched = [self._enrich_article(a, a.get("source", "")) for a in articles]
        enriched.sort(key=lambda a: (a.get("source_reliability", 0), a["published_at"]), reverse=True)
        return enriched[:limit]
