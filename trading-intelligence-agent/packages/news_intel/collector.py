"""News collector — orchestrates ingestion from multiple providers."""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

import structlog

from packages.data_providers.base import BaseNewsProvider
from packages.social_intel.ticker_extractor import TickerExtractor
from packages.social_intel.sentiment import NewsCredibilityScorer, SentimentScorer
from packages.storage.repositories import NewsRepository, RawPayloadRepository

logger = structlog.get_logger()

_extractor = TickerExtractor()
_sentiment = SentimentScorer()
_cred = NewsCredibilityScorer()


class NewsCollector:
    def __init__(self, providers: list[BaseNewsProvider], db_session_factory: Any) -> None:
        self.providers = providers
        self.db_factory = db_session_factory

    def _enrich(self, article: dict[str, Any]) -> dict[str, Any]:
        text = (article.get("title", "") + " " + (article.get("raw_text") or ""))
        if not article.get("tickers_mentioned"):
            article["tickers_mentioned"] = _extractor.extract(text)
        pub_raw = article.get("published_at", "")
        try:
            pub_dt = datetime.fromisoformat(str(pub_raw).replace("Z", "+00:00"))
            hours_ago = (datetime.now(tz=timezone.utc) - pub_dt).total_seconds() / 3600
        except Exception:
            hours_ago = 0.0
        article["credibility_score"] = _cred.score_article(
            article.get("title", ""),
            article.get("source", ""),
            hours_ago,
        )
        return article

    async def collect_for_watchlist(
        self, symbols: list[str], hours_back: int = 24,
    ) -> dict[str, Any]:
        summary: dict[str, Any] = {}
        async with self.db_factory() as db:
            raw_repo = RawPayloadRepository(db)
            news_repo = NewsRepository(db)
            for provider in self.providers:
                t0 = time.monotonic()
                fetched = new_count = dup_count = errors = 0
                try:
                    articles = await provider.fetch_for_symbols(
                        symbols, limit_per_symbol=10, hours_back=hours_back,
                    )
                    for raw_art in articles:
                        fetched += 1
                        enriched = self._enrich(dict(raw_art))
                        try:
                            await raw_repo.store(
                                provider.config.name, "news_article",
                                enriched.get("url", "unknown"),
                                {"title": enriched.get("title"), "url": enriched.get("url")},
                            )
                            _, created = await news_repo.upsert_by_hash(enriched)
                            if created:
                                new_count += 1
                            else:
                                dup_count += 1
                        except Exception as exc:  # noqa: BLE001
                            errors += 1
                            logger.warning("news_upsert_failed", error=str(exc))
                    ms = int((time.monotonic() - t0) * 1000)
                    logger.info(
                        "news_collected",
                        provider=provider.config.name,
                        fetched=fetched, new=new_count, dupes=dup_count, errors=errors, ms=ms,
                    )
                    summary[provider.config.name] = {
                        "articles_fetched": fetched,
                        "new_articles": new_count,
                        "duplicate_articles": dup_count,
                        "errors": errors,
                    }
                except Exception as exc:  # noqa: BLE001
                    ms = int((time.monotonic() - t0) * 1000)
                    logger.error("news_provider_failed", provider=provider.config.name, error=str(exc), ms=ms)
                    summary[provider.config.name] = {"articles_fetched": 0, "new_articles": 0,
                                                      "duplicate_articles": 0, "errors": 1}
            await db.commit()
        return summary

    async def collect_general_market_news(self, hours_back: int = 24) -> dict[str, Any]:
        generic_symbols = ["market", "S&P", "Federal Reserve", "economy", "inflation"]
        return await self.collect_for_watchlist(generic_symbols, hours_back=hours_back)

    async def compute_symbol_sentiment(
        self, symbol: str, db: Any, hours_back: int = 48,
    ) -> dict[str, Any]:
        news_repo = NewsRepository(db)
        articles = await news_repo.get_by_symbol(symbol, limit=50, hours_back=hours_back)
        if not articles:
            return {
                "symbol": symbol, "article_count": 0, "avg_sentiment": 0.0,
                "bullish_count": 0, "bearish_count": 0, "neutral_count": 0,
                "top_headlines": [], "latest_fetched_at": None,
                "credibility_weighted_sentiment": 0.0,
            }
        scores = []
        cred_weighted = []
        headlines = []
        bull = bear = neutral = 0
        for a in articles:
            text = (a.title or "") + " " + (a.raw_text or a.summary or "")
            score = _sentiment.score_text(text)
            cred = float(a.credibility_score or 0.5)
            scores.append(score)
            cred_weighted.append(score * cred)
            headlines.append(a.title or "")
            direction = _sentiment.classify_sentiment(score)
            if direction.value == "bullish":
                bull += 1
            elif direction.value == "bearish":
                bear += 1
            else:
                neutral += 1
        avg = sum(scores) / len(scores) if scores else 0.0
        cred_avg = sum(cred_weighted) / len(cred_weighted) if cred_weighted else 0.0
        latest = max((a.fetched_at for a in articles), default=None)
        return {
            "symbol": symbol, "article_count": len(articles),
            "avg_sentiment": round(avg, 3),
            "bullish_count": bull, "bearish_count": bear, "neutral_count": neutral,
            "top_headlines": headlines[:5],
            "latest_fetched_at": latest.isoformat() if latest else None,
            "credibility_weighted_sentiment": round(cred_avg, 3),
        }
