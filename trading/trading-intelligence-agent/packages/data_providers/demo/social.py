"""Demo social provider — fixture Reddit-style posts."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import xxhash
import structlog

from packages.data_providers.base import BaseSocialProvider, ProviderConfig

logger = structlog.get_logger()
_NOW = datetime.now(tz=timezone.utc)


def _ah(n: int) -> str:
    return xxhash.xxh64(f"demo_user_{n}".encode()).hexdigest()[:12]


def _iso(dt: datetime) -> str:
    return dt.isoformat()


_POSTS: list[dict[str, Any]] = [
    {
        "platform": "reddit", "source_community": "r/investing",
        "author_hash": _ah(1), "url": "https://reddit.com/r/investing/demo/1",
        "posted_at": _iso(_NOW - timedelta(hours=2)), "fetched_at": _iso(_NOW),
        "text": "Long-term bull case for NVDA: AI capex cycle is structural. Adding on any dip below $800.",
        "tickers_mentioned": ["NVDA"], "assets_mentioned": ["NVDA"],
        "engagement_score": 0.82, "credibility_score": 0.65,
        "sentiment_score": 0.8, "toxicity_or_spam_score": 0.05,
    },
    {
        "platform": "reddit", "source_community": "r/wallstreetbets",
        "author_hash": _ah(2), "url": "https://reddit.com/r/wallstreetbets/demo/2",
        "posted_at": _iso(_NOW - timedelta(hours=4)), "fetched_at": _iso(_NOW),
        "text": "YOLO'd my 401k into TSLA 0DTE calls. Either I retire next week or ramen for a year 🚀🚀🚀",
        "tickers_mentioned": ["TSLA"], "assets_mentioned": ["TSLA"],
        "engagement_score": 0.91, "credibility_score": 0.2,
        "sentiment_score": 0.9, "toxicity_or_spam_score": 0.3,
    },
    {
        "platform": "reddit", "source_community": "r/stocks",
        "author_hash": _ah(3), "url": "https://reddit.com/r/stocks/demo/3",
        "posted_at": _iso(_NOW - timedelta(hours=6)), "fetched_at": _iso(_NOW),
        "text": "DD: Apple Services is 25% of revenue at 40%+ gross margins. With 2.2B devices, Services flywheel is accelerating.",
        "tickers_mentioned": ["AAPL"], "assets_mentioned": ["AAPL"],
        "engagement_score": 0.74, "credibility_score": 0.6,
        "sentiment_score": 0.7, "toxicity_or_spam_score": 0.02,
    },
    {
        "platform": "reddit", "source_community": "r/CryptoCurrency",
        "author_hash": _ah(4), "url": "https://reddit.com/r/CryptoCurrency/demo/4",
        "posted_at": _iso(_NOW - timedelta(hours=8)), "fetched_at": _iso(_NOW),
        "text": "ETH ETF approval is massive. Institutions get clean ETH exposure. Expect $5-10B AUM year one.",
        "tickers_mentioned": ["ETH-USD", "BTC-USD"], "assets_mentioned": ["ETH-USD"],
        "engagement_score": 0.78, "credibility_score": 0.45,
        "sentiment_score": 0.75, "toxicity_or_spam_score": 0.04,
    },
    {
        "platform": "reddit", "source_community": "r/wallstreetbets",
        "author_hash": _ah(5), "url": "https://reddit.com/r/wallstreetbets/demo/5",
        "posted_at": _iso(_NOW - timedelta(hours=10)), "fetched_at": _iso(_NOW),
        "text": "SPY puts printing. Fed said higher for longer. Bears finally win. Loading TLT.",
        "tickers_mentioned": ["SPY", "TLT"], "assets_mentioned": ["SPY", "TLT"],
        "engagement_score": 0.55, "credibility_score": 0.25,
        "sentiment_score": -0.6, "toxicity_or_spam_score": 0.2,
    },
    {
        "platform": "reddit", "source_community": "r/investing",
        "author_hash": _ah(6), "url": "https://reddit.com/r/investing/demo/6",
        "posted_at": _iso(_NOW - timedelta(hours=14)), "fetched_at": _iso(_NOW),
        "text": "Tesla US market share fell from 62% to 51% YoY. Valuation at 70x earnings is unjustifiable.",
        "tickers_mentioned": ["TSLA"], "assets_mentioned": ["TSLA"],
        "engagement_score": 0.68, "credibility_score": 0.7,
        "sentiment_score": -0.4, "toxicity_or_spam_score": 0.03,
    },
    {
        "platform": "reddit", "source_community": "r/investing",
        "author_hash": _ah(10), "url": "https://reddit.com/r/investing/demo/10",
        "posted_at": _iso(_NOW - timedelta(hours=20)), "fetched_at": _iso(_NOW),
        "text": "2y/10y curve inverted 22 months — longest in history. Every recession since 1955 was preceded by inversion.",
        "tickers_mentioned": ["SPY", "TLT", "QQQ"], "assets_mentioned": ["SPY", "TLT"],
        "engagement_score": 0.77, "credibility_score": 0.67,
        "sentiment_score": -0.5, "toxicity_or_spam_score": 0.02,
    },
]


class DemoSocialProvider(BaseSocialProvider):
    def __init__(self) -> None:
        super().__init__(ProviderConfig(name="demo_social", demo_mode=True))

    async def fetch_posts(
        self, query: str = "", subreddit_or_community: str = "",
        limit: int = 20, hours_back: int = 24,
    ) -> list[dict[str, Any]]:
        cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=hours_back)
        q = query.upper()
        community = subreddit_or_community.lower()
        filtered = []
        for p in _POSTS:
            posted = datetime.fromisoformat(p["posted_at"])
            if posted < cutoff:
                continue
            if community and community not in p["source_community"].lower():
                continue
            if not q or q in [t.upper() for t in p["tickers_mentioned"]] or q in p["text"].upper():
                filtered.append(p)
        if not filtered:
            filtered = [p for p in _POSTS if datetime.fromisoformat(p["posted_at"]) >= cutoff]
        return filtered[:limit]
