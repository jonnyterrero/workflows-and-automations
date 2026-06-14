"""Crypto-focused RSS news — CoinDesk, Cointelegraph, Bloomberg Crypto, etc."""
from __future__ import annotations

import os
from typing import Any

from packages.data_providers.live.rss_news import RssNewsProvider

# Reputable free crypto news RSS feeds (user can override via CRYPTO_RSS_FEED_URLS)
_DEFAULT_CRYPTO_FEEDS: list[tuple[str, str]] = [
    ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
    ("Cointelegraph", "https://cointelegraph.com/rss"),
    ("Decrypt", "https://decrypt.co/feed"),
    ("Bitcoin Magazine", "https://bitcoinmagazine.com/.rss/full/"),
    ("Bloomberg Crypto", "https://feeds.bloomberg.com/crypto/news.rss"),
    ("The Block", "https://www.theblock.co/rss.xml"),
]


class CryptoRssNewsProvider(RssNewsProvider):
    """RSS provider scoped to verified crypto news outlets."""

    def __init__(self, feed_urls: list[str] | None = None) -> None:
        env_feeds = os.getenv("CRYPTO_RSS_FEED_URLS", "")
        if feed_urls:
            feeds = [(url.split("/")[2] if "/" in url else f"Crypto-{i}", url)
                     for i, url in enumerate(feed_urls)]
        elif env_feeds.strip():
            urls = [u.strip() for u in env_feeds.split(",") if u.strip()]
            feeds = [(u.split("/")[2] if "/" in u else f"Crypto-{i}", u) for i, u in enumerate(urls)]
        else:
            feeds = list(_DEFAULT_CRYPTO_FEEDS)

        # Initialize parent with explicit feed list; override provider name
        super().__init__(feed_urls=[url for _, url in feeds])
        self._feeds = feeds
        self.config.name = "crypto_rss_news"

    async def fetch_articles(self, query: str = "", limit: int = 20, hours_back: int = 48) -> list[dict[str, Any]]:
        articles = await super().fetch_articles(query=query, limit=limit, hours_back=hours_back)
        for article in articles:
            # Crypto outlets get slightly higher default credibility
            if article.get("credibility_score", 0) < 0.7:
                src = (article.get("source") or "").lower()
                if any(k in src for k in ("coindesk", "bloomberg", "block", "cointelegraph")):
                    article["credibility_score"] = 0.78
        return articles
