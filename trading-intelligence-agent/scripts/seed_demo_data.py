"""Seed the database with the PDF-defined asset universe and demo fixtures."""
from __future__ import annotations

import asyncio
import os
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import xxhash

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from packages.policy.defaults import (  # noqa: E402
    ASSET_UNIVERSE,
    DEFAULT_POLICY_RULES,
    DEFAULT_PORTFOLIO_POSITIONS,
    DEFAULT_PROFILE,
)
from packages.storage.database import AsyncSessionLocal, create_tables  # noqa: E402
from packages.storage.repositories import (  # noqa: E402
    AssetRepository,
    MacroRepository,
    MarketPriceRepository,
    NewsRepository,
    PortfolioPolicyRepository,
    PortfolioProfileRepository,
    SocialPostRepository,
)


DEMO_MACRO: list[dict[str, object]] = [
    {"series_id": "fed_funds_rate", "value": 5.25, "unit": "percent", "category": "monetary_policy"},
    {"series_id": "cpi_yoy", "value": 3.20, "unit": "percent", "category": "inflation"},
    {"series_id": "gdp_growth_qoq", "value": 2.10, "unit": "percent", "category": "growth"},
    {"series_id": "unemployment_rate", "value": 4.10, "unit": "percent", "category": "labor"},
    {"series_id": "10y_treasury_yield", "value": 4.38, "unit": "percent", "category": "rates"},
    {"series_id": "2y_treasury_yield", "value": 4.75, "unit": "percent", "category": "rates"},
    {"series_id": "vix", "value": 16.4, "unit": "index", "category": "volatility"},
    {"series_id": "dxy", "value": 103.2, "unit": "index", "category": "forex"},
]


def _base_price(asset_class: str) -> float:
    return {
        "ETF": 80.0,
        "EQUITY": 120.0,
        "CRYPTO": 240.0,
        "BOND": 95.0,
        "CASH_EQUIVALENT": 100.0,
        "METAL": 60.0,
    }.get(asset_class, 75.0)


def _build_price_history(symbol: str, asset_class: str, trading_days: int = 260) -> list[dict[str, object]]:
    seed = int(xxhash.xxh32(symbol.encode()).hexdigest(), 16)
    rng = random.Random(seed)
    current = _base_price(asset_class)
    rows: list[dict[str, object]] = []
    today = datetime.now(tz=timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    for day_offset in range(trading_days, 0, -1):
        timestamp = today - timedelta(days=day_offset)
        if timestamp.weekday() >= 5:
            continue

        drift = 0.0005
        volatility = 0.018 if asset_class != "CRYPTO" else 0.035
        daily_return = drift + rng.uniform(-volatility, volatility)
        close = max(current * (1 + daily_return), 5.0)
        open_price = current
        high = max(open_price, close) * (1 + rng.uniform(0.001, 0.018))
        low = min(open_price, close) * (1 - rng.uniform(0.001, 0.018))
        volume = rng.randint(1_000_000, 12_000_000)
        rows.append(
            {
                "symbol": symbol,
                "timestamp": timestamp,
                "open": round(open_price, 2),
                "high": round(high, 2),
                "low": round(low, 2),
                "close": round(close, 2),
                "adjusted_close": round(close, 2),
                "volume": float(volume),
                "source": "demo_seed",
                "interval": "1d",
            }
        )
        current = close
    return rows


async def seed() -> None:
    await create_tables()

    async with AsyncSessionLocal() as db:
        asset_repo = AssetRepository(db)
        price_repo = MarketPriceRepository(db)
        macro_repo = MacroRepository(db)
        news_repo = NewsRepository(db)
        social_repo = SocialPostRepository(db)
        profile_repo = PortfolioProfileRepository(db)
        policy_repo = PortfolioPolicyRepository(db)

        print("Seeding asset universe...")
        for asset in ASSET_UNIVERSE:
            asset_class = asset["asset_class"].value if hasattr(asset["asset_class"], "value") else str(asset["asset_class"])
            row = await asset_repo.upsert(
                SimpleNamespace(
                    symbol=asset["symbol"],
                    name=asset["name"],
                    asset_class=asset["asset_class"],
                    exchange="NASDAQ" if asset_class != "CRYPTO" else "CRYPTO",
                    currency="USD",
                    sector=asset.get("sector"),
                    industry=asset.get("sector"),
                    theme_tags=asset.get("theme_tags", []),
                    metadata={"is_speculative": asset.get("is_speculative", False)},
                    is_active=True,
                )
            )
            if row.symbol in {"VOO", "VXUS", "QQQM", "SMH", "NLR", "GLD", "IBIT", "SGOV"}:
                await asset_repo.add_to_watchlist(row.id, notes="Seeded default watchlist asset")
            print(f"  - {row.symbol}")

        print("Seeding synthetic OHLCV history...")
        for asset in ASSET_UNIVERSE:
            asset_class = asset["asset_class"].value if hasattr(asset["asset_class"], "value") else str(asset["asset_class"])
            prices = _build_price_history(str(asset["symbol"]), asset_class)
            await price_repo.bulk_upsert(prices)
        print(f"  - seeded price bars for {len(ASSET_UNIVERSE)} assets")

        print("Seeding macro indicators...")
        now = datetime.now(tz=timezone.utc)
        for entry in DEMO_MACRO:
            await macro_repo.upsert(
                str(entry["series_id"]),
                [
                    {
                        "value": float(entry["value"]),
                        "unit": str(entry["unit"]),
                        "category": str(entry["category"]),
                        "source": "demo_seed",
                        "observation_date": now.isoformat(),
                    }
                ],
            )
            print(f"  - {entry['series_id']}")

        print("Seeding research fixtures...")
        demo_news = [
            {
                "source": "Reuters",
                "author": "Reuters Staff",
                "title": "NVIDIA AI Infrastructure Demand Holds Up in Demo Dataset",
                "url": "https://example.test/news/nvda-ai-demand",
                "published_at": now.isoformat(),
                "fetched_at": now.isoformat(),
                "summary": "Synthetic seed article describing resilient AI demand.",
                "content_hash": xxhash.xxh64("seed-nvda-news".encode()).hexdigest(),
                "tickers_mentioned": ["NVDA", "SMH"],
                "assets_mentioned": ["NVDA", "SMH"],
                "raw_text": "AI infrastructure demand remains firm, but valuations are elevated.",
                "credibility_score": 0.90,
            },
            {
                "source": "Bloomberg",
                "author": "Macro Desk",
                "title": "Treasury Yields Stay Restrictive in Demo Macro Tape",
                "url": "https://example.test/news/yields-restrictive",
                "published_at": now.isoformat(),
                "fetched_at": now.isoformat(),
                "summary": "Synthetic macro article describing a restrictive rate regime.",
                "content_hash": xxhash.xxh64("seed-macro-news".encode()).hexdigest(),
                "tickers_mentioned": ["BND", "SGOV", "SMH"],
                "assets_mentioned": ["BND", "SGOV", "SMH"],
                "raw_text": "Rates remain restrictive and valuation risk matters more for crowded growth trades.",
                "credibility_score": 0.92,
            },
        ]
        for article in demo_news:
            await news_repo.upsert_by_hash(article)

        demo_posts = [
            {
                "platform": "reddit",
                "source_community": "r/investing",
                "author_hash": xxhash.xxh64("seed-user-1".encode()).hexdigest()[:12],
                "url": "https://reddit.example.test/post/1",
                "posted_at": now.isoformat(),
                "fetched_at": now.isoformat(),
                "text": "SMH still has a long-term AI case, but I would not chase a crowded move here.",
                "tickers_mentioned": ["SMH"],
                "assets_mentioned": ["SMH"],
                "engagement_score": 0.71,
                "credibility_score": 0.55,
                "sentiment_score": 0.34,
                "toxicity_or_spam_score": 0.05,
            },
            {
                "platform": "reddit",
                "source_community": "r/cryptocurrency",
                "author_hash": xxhash.xxh64("seed-user-2".encode()).hexdigest()[:12],
                "url": "https://reddit.example.test/post/2",
                "posted_at": now.isoformat(),
                "fetched_at": now.isoformat(),
                "text": "Bitcoin ETF flows are still strong, but this is obviously a high-volatility risk asset.",
                "tickers_mentioned": ["BTC", "IBIT"],
                "assets_mentioned": ["BTC", "IBIT"],
                "engagement_score": 0.66,
                "credibility_score": 0.45,
                "sentiment_score": 0.52,
                "toxicity_or_spam_score": 0.08,
            },
        ]
        for post in demo_posts:
            await social_repo.upsert(post)

        print("Seeding default portfolio profile and rules...")
        profile_row = await profile_repo.upsert(DEFAULT_PROFILE)
        await profile_repo.set_positions(profile_row.id, DEFAULT_PORTFOLIO_POSITIONS)
        await policy_repo.replace_rules(profile_row.id, DEFAULT_POLICY_RULES)
        print(f"  - profile {profile_row.name}")

    print("\nTrading intelligence demo seed complete.")
    print("Run `uvicorn apps.api_service.main:app --reload --host 0.0.0.0 --port 8000` to start the API.")


if __name__ == "__main__":
    asyncio.run(seed())
