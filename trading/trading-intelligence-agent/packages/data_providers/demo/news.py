"""Demo news provider — returns hard-coded fixture articles."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import xxhash
import structlog

from packages.data_providers.base import BaseNewsProvider, ProviderConfig

logger = structlog.get_logger()
_NOW = datetime.now(tz=timezone.utc)


def _h(text: str) -> str:
    return xxhash.xxh64(text.encode()).hexdigest()


def _iso(dt: datetime) -> str:
    return dt.isoformat()


_ARTICLES: list[dict[str, Any]] = [
    {
        "source": "Reuters", "author": "Reuters Staff",
        "title": "NVIDIA Posts Record Quarter, Beats Estimates on AI Chip Demand",
        "url": "https://demo.reuters.com/nvda-q4",
        "published_at": _iso(_NOW - timedelta(hours=3)), "fetched_at": _iso(_NOW),
        "summary": "NVIDIA Q4 revenue $26B, beats $24.5B consensus, data center +409% YoY.",
        "content_hash": _h("nvda-q4-record"),
        "tickers_mentioned": ["NVDA"], "assets_mentioned": ["NVDA"],
        "raw_text": "NVIDIA Corporation reported record Q4 revenue of $26B driven by H100 GPU demand.",
        "credibility_score": 0.9,
    },
    {
        "source": "Bloomberg", "author": "John Smith",
        "title": "Fed Signals Higher-for-Longer Rate Path Amid Sticky Inflation",
        "url": "https://demo.bloomberg.com/fed-hlfl",
        "published_at": _iso(_NOW - timedelta(hours=8)), "fetched_at": _iso(_NOW),
        "summary": "Fed chair signals no rush to cut rates. CPI at 3.2%.",
        "content_hash": _h("fed-higher-for-longer"),
        "tickers_mentioned": ["SPY", "QQQ", "TLT"], "assets_mentioned": ["SPY", "QQQ", "TLT"],
        "raw_text": "Fed Chair Powell reiterated rates will stay elevated while inflation remains above 2%.",
        "credibility_score": 0.9,
    },
    {
        "source": "Yahoo Finance", "author": "Finance Desk",
        "title": "Apple Unveils Vision Pro 2 at WWDC, Stock Jumps 3%",
        "url": "https://demo.finance.yahoo.com/aapl-vp2",
        "published_at": _iso(_NOW - timedelta(hours=12)), "fetched_at": _iso(_NOW),
        "summary": "Apple Vision Pro 2: lighter, longer battery, AAPL +3% after-hours.",
        "content_hash": _h("aapl-vp2-wwdc"),
        "tickers_mentioned": ["AAPL"], "assets_mentioned": ["AAPL"],
        "raw_text": "Apple announced Vision Pro 2 with 40% lighter design and 4h battery.",
        "credibility_score": 0.7,
    },
    {
        "source": "Bloomberg", "author": "Crypto Desk",
        "title": "SEC Approves Ethereum Spot ETF Applications from BlackRock, Fidelity",
        "url": "https://demo.bloomberg.com/eth-etf-approval",
        "published_at": _iso(_NOW - timedelta(hours=18)), "fetched_at": _iso(_NOW),
        "summary": "Spot ETH ETF approved, ETH surges 12%.",
        "content_hash": _h("eth-etf-approval-sec"),
        "tickers_mentioned": ["ETH-USD", "BTC-USD"], "assets_mentioned": ["ETH-USD"],
        "raw_text": "SEC approved spot Ethereum ETFs from BlackRock and Fidelity. ETH +12%.",
        "credibility_score": 0.9,
    },
    {
        "source": "Reuters", "author": "Auto Desk",
        "title": "Tesla Cuts Model 3 Price in US and Europe Amid EV Price War",
        "url": "https://demo.reuters.com/tsla-price-cut",
        "published_at": _iso(_NOW - timedelta(hours=24)), "fetched_at": _iso(_NOW),
        "summary": "Tesla reduces Model 3 prices by $2000 amid BYD competition.",
        "content_hash": _h("tsla-m3-price-cut"),
        "tickers_mentioned": ["TSLA"], "assets_mentioned": ["TSLA"],
        "raw_text": "Tesla cut Model 3 prices by $2000 in US. Base now $38,990.",
        "credibility_score": 0.9,
    },
    {
        "source": "CoinDesk", "author": "Crypto Reporter",
        "title": "Bitcoin Halving Approaches: Historical Price Patterns Reviewed",
        "url": "https://demo.coindesk.com/btc-halving",
        "published_at": _iso(_NOW - timedelta(hours=36)), "fetched_at": _iso(_NOW),
        "summary": "BTC halving in ~30 days. Historical: +300% avg in 12mo post-halving.",
        "content_hash": _h("btc-halving-history-review"),
        "tickers_mentioned": ["BTC-USD"], "assets_mentioned": ["BTC-USD"],
        "raw_text": "Bitcoin block reward halves in 30 days. 2016/2020 halvings saw 300%+ gains.",
        "credibility_score": 0.65,
    },
    {
        "source": "Random Finance Blog", "author": "anon_99",
        "title": "Why SPY Will Crash 50% Next Month (Elliott Wave Analysis)",
        "url": "https://randomfinanceblog.net/spy-crash",
        "published_at": _iso(_NOW - timedelta(hours=48)), "fetched_at": _iso(_NOW),
        "summary": "Obscure blogger predicts 50% crash using Elliott Wave.",
        "content_hash": _h("spy-crash-prediction-blog"),
        "tickers_mentioned": ["SPY", "TLT"], "assets_mentioned": ["SPY"],
        "raw_text": "Elliott Wave analysis shows SPY completing Wave 5 top. 50% correction incoming.",
        "credibility_score": 0.2,
    },
]


class DemoNewsProvider(BaseNewsProvider):
    def __init__(self) -> None:
        super().__init__(ProviderConfig(name="demo_news", demo_mode=True))

    async def fetch_articles(
        self, query: str = "", limit: int = 20, hours_back: int = 24,
    ) -> list[dict[str, Any]]:
        cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=hours_back)
        q = query.upper()
        filtered = []
        for a in _ARTICLES:
            pub = datetime.fromisoformat(a["published_at"])
            if pub < cutoff:
                continue
            if not q or q in [t.upper() for t in a["tickers_mentioned"]] or q in a["title"].upper():
                filtered.append(a)
        if not filtered:
            filtered = [a for a in _ARTICLES if datetime.fromisoformat(a["published_at"]) >= cutoff]
        return filtered[:limit]
