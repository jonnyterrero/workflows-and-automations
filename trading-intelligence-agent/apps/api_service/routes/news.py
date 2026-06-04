"""News and social post routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from packages.news_intel.collector import NewsCollector
from packages.storage.database import get_db
from packages.storage.repositories import NewsRepository, SocialPostRepository

router = APIRouter()


@router.get("")
async def list_news(
    hours_back: int = Query(24, description="Hours to look back"),
    limit: int = Query(50, description="Max articles"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    repo = NewsRepository(db)
    articles = await repo.get_recent(limit=limit, hours_back=hours_back)
    return {
        "count": len(articles),
        "hours_back": hours_back,
        "articles": [
            {
                "id": a.id, "source": a.source, "title": a.title,
                "url": a.url, "published_at": a.published_at.isoformat(),
                "tickers_mentioned": a.tickers_mentioned or [],
                "credibility_score": a.credibility_score,
                "summary": a.summary,
            }
            for a in articles
        ],
    }


@router.get("/{symbol}")
async def get_news_for_symbol(
    symbol: str,
    hours_back: int = Query(72, description="Hours to look back"),
    limit: int = Query(20, description="Max articles"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    repo = NewsRepository(db)
    articles = await repo.get_by_symbol(symbol.upper(), limit=limit, hours_back=hours_back)
    collector = NewsCollector([], None)  # type: ignore
    sentiment = await collector.compute_symbol_sentiment(symbol.upper(), db, hours_back=hours_back)
    return {
        "symbol": symbol.upper(),
        "count": len(articles),
        "sentiment_summary": sentiment,
        "articles": [
            {
                "id": a.id, "source": a.source, "title": a.title,
                "published_at": a.published_at.isoformat(),
                "credibility_score": a.credibility_score,
                "summary": a.summary,
            }
            for a in articles
        ],
    }


@router.get("/social/trending")
async def get_trending_social(
    hours_back: int = Query(12, description="Hours to look back"),
    limit: int = Query(20, description="Max posts"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    repo = SocialPostRepository(db)
    posts = await repo.get_trending(limit=limit, hours_back=hours_back)
    return {
        "count": len(posts),
        "posts": [
            {
                "id": p.id, "platform": p.platform,
                "source_community": p.source_community,
                "text": p.text[:200],
                "tickers_mentioned": p.tickers_mentioned or [],
                "engagement_score": p.engagement_score,
                "sentiment_score": p.sentiment_score,
                "toxicity_or_spam_score": p.toxicity_or_spam_score,
            }
            for p in posts
        ],
    }


@router.get("/social/{symbol}")
async def get_social_for_symbol(
    symbol: str,
    hours_back: int = Query(48, description="Hours to look back"),
    limit: int = Query(20, description="Max posts"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    repo = SocialPostRepository(db)
    posts = await repo.get_by_symbol(symbol.upper(), limit=limit, hours_back=hours_back)
    return {
        "symbol": symbol.upper(),
        "count": len(posts),
        "posts": [
            {
                "id": p.id, "platform": p.platform,
                "source_community": p.source_community,
                "text": p.text[:200],
                "sentiment_score": p.sentiment_score,
                "toxicity_or_spam_score": p.toxicity_or_spam_score,
                "engagement_score": p.engagement_score,
                "posted_at": p.posted_at.isoformat(),
            }
            for p in posts
        ],
    }
