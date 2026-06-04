"""Seed the database with demo watchlist assets and fixture data."""
from __future__ import annotations

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from packages.storage.database import create_tables, AsyncSessionLocal
from packages.storage.repositories import (
    AssetRepository, MacroRepository, NewsRepository, SocialPostRepository,
)
from packages.core_models.pydantic_models import AssetClass, AssetCreate

WATCHLIST_ASSETS: list[dict] = [
    {"symbol": "SPY",     "name": "SPDR S&P 500 ETF Trust",         "asset_class": AssetClass.ETF,    "exchange": "NYSE", "sector": "Broad Market"},
    {"symbol": "QQQ",     "name": "Invesco QQQ Trust",              "asset_class": AssetClass.ETF,    "exchange": "NASDAQ", "sector": "Technology"},
    {"symbol": "TLT",     "name": "iShares 20+ Year Treasury Bond", "asset_class": AssetClass.BOND_ETF, "exchange": "NYSE", "sector": "Fixed Income"},
    {"symbol": "AAPL",    "name": "Apple Inc.",                     "asset_class": AssetClass.STOCK,  "exchange": "NASDAQ", "sector": "Technology", "industry": "Consumer Electronics"},
    {"symbol": "NVDA",    "name": "NVIDIA Corporation",             "asset_class": AssetClass.STOCK,  "exchange": "NASDAQ", "sector": "Technology", "industry": "Semiconductors"},
    {"symbol": "TSLA",    "name": "Tesla Inc.",                     "asset_class": AssetClass.STOCK,  "exchange": "NASDAQ", "sector": "Consumer Discretionary", "industry": "Electric Vehicles"},
    {"symbol": "BTC-USD", "name": "Bitcoin / US Dollar",            "asset_class": AssetClass.CRYPTO, "exchange": "Crypto", "currency": "USD"},
    {"symbol": "ETH-USD", "name": "Ethereum / US Dollar",           "asset_class": AssetClass.CRYPTO, "exchange": "Crypto", "currency": "USD"},
]

DEMO_MACRO: list[dict] = [
    {"series_id": "fed_funds_rate",    "value": 5.25, "unit": "percent", "category": "monetary_policy"},
    {"series_id": "cpi_yoy",           "value": 3.2,  "unit": "percent", "category": "inflation"},
    {"series_id": "gdp_growth_qoq",    "value": 2.1,  "unit": "percent", "category": "growth"},
    {"series_id": "10y_treasury_yield","value": 4.38, "unit": "percent", "category": "rates"},
    {"series_id": "2y_treasury_yield", "value": 4.75, "unit": "percent", "category": "rates"},
    {"series_id": "vix",               "value": 15.0, "unit": "index",   "category": "volatility"},
    {"series_id": "dxy",               "value": 103.5,"unit": "index",   "category": "forex"},
]


async def seed() -> None:
    print("Creating tables...")
    await create_tables()

    async with AsyncSessionLocal() as db:
        asset_repo = AssetRepository(db)
        macro_repo = MacroRepository(db)
        news_repo  = NewsRepository(db)
        social_repo = SocialPostRepository(db)

        # Seed watchlist assets
        print("Seeding watchlist assets...")
        for a in WATCHLIST_ASSETS:
            asset = AssetCreate(
                symbol=a["symbol"],
                name=a["name"],
                asset_class=a["asset_class"],
                exchange=a.get("exchange"),
                currency=a.get("currency", "USD"),
                sector=a.get("sector"),
                industry=a.get("industry"),
            )
            row = await asset_repo.upsert(asset)
            await asset_repo.add_to_watchlist(row.id, notes="default watchlist")
            print(f"  ✓ {a['symbol']}")

        # Seed macro indicators
        print("Seeding macro indicators...")
        from datetime import datetime, timezone
        now = datetime.now(tz=timezone.utc)
        for m in DEMO_MACRO:
            await macro_repo.upsert(m["series_id"], [{
                "value": m["value"],
                "unit": m["unit"],
                "category": m["category"],
                "source": "demo_seed",
                "observation_date": now.isoformat(),
            }])
            print(f"  ✓ {m['series_id']}: {m['value']}")

        # Seed sample news
        print("Seeding demo news articles...")
        import xxhash
        demo_news = [
            {
                "source": "Reuters", "author": "Reuters Staff",
                "title": "NVIDIA Posts Record Quarter on AI Chip Demand (demo seed)",
                "url": "https://demo.reuters.com/nvda-record",
                "published_at": now.isoformat(), "fetched_at": now.isoformat(),
                "summary": "Demo: NVDA beat estimates on AI chip demand.",
                "content_hash": xxhash.xxh64("nvda-record-demo".encode()).hexdigest(),
                "tickers_mentioned": ["NVDA"], "assets_mentioned": ["NVDA"],
                "raw_text": "Demo article for seeding.", "credibility_score": 0.9,
            },
            {
                "source": "Bloomberg", "author": "Macro Desk",
                "title": "Fed Signals Higher-for-Longer Rate Path (demo seed)",
                "url": "https://demo.bloomberg.com/fed-hlfl",
                "published_at": now.isoformat(), "fetched_at": now.isoformat(),
                "summary": "Demo: Fed to hold rates through Q3.",
                "content_hash": xxhash.xxh64("fed-hlfl-demo".encode()).hexdigest(),
                "tickers_mentioned": ["SPY", "TLT"], "assets_mentioned": ["SPY", "TLT"],
                "raw_text": "Demo macro article.", "credibility_score": 0.9,
            },
        ]
        for article in demo_news:
            _, created = await news_repo.upsert_by_hash(article)
            status = "created" if created else "exists"
            print(f"  ✓ {article['title'][:50]}... ({status})")

        # Seed sample social posts
        print("Seeding demo social posts...")
        import xxhash as _xxhash
        demo_posts = [
            {
                "platform": "reddit", "source_community": "r/investing",
                "author_hash": _xxhash.xxh64("seed_user_1".encode()).hexdigest()[:12],
                "url": "https://reddit.com/demo/post1",
                "posted_at": now.isoformat(), "fetched_at": now.isoformat(),
                "text": "Long-term bull case for NVDA remains intact. AI capex cycle is structural.",
                "tickers_mentioned": ["NVDA"], "assets_mentioned": ["NVDA"],
                "engagement_score": 0.75, "credibility_score": 0.6,
                "sentiment_score": 0.8, "toxicity_or_spam_score": 0.02,
            },
        ]
        for post in demo_posts:
            _, created = await social_repo.upsert(post)
            status = "created" if created else "exists"
            print(f"  ✓ social post ({status})")

        await db.commit()

    print("\n✓ Demo data seeded successfully.")
    print("Run 'make run-api' or 'make run-demo' to start the API.")


if __name__ == "__main__":
    asyncio.run(seed())
