"""Social collector — orchestrates ingestion from Reddit, X, and other social providers."""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

import structlog

from packages.data_providers.base import BaseSocialProvider
from packages.social_intel.ticker_extractor import TickerExtractor
from packages.social_intel.sentiment import SentimentScorer
from packages.storage.repositories import RawPayloadRepository, SocialPostRepository

logger = structlog.get_logger()

_extractor = TickerExtractor()
_sentiment = SentimentScorer()


class SocialCollector:
    def __init__(self, providers: list[BaseSocialProvider], db_session_factory: Any) -> None:
        self.providers = providers
        self.db_factory = db_session_factory

    def _enrich(self, post: dict[str, Any]) -> dict[str, Any]:
        text = post.get("text", "")
        if not post.get("tickers_mentioned"):
            post["tickers_mentioned"] = _extractor.extract(text)
        if post.get("sentiment_score", 0.0) == 0.0:
            post["sentiment_score"] = _sentiment.score_text(text)
        return post

    async def collect_for_watchlist(
        self, symbols: list[str], hours_back: int = 24,
    ) -> dict[str, Any]:
        summary: dict[str, Any] = {}
        async with self.db_factory() as db:
            raw_repo = RawPayloadRepository(db)
            social_repo = SocialPostRepository(db)
            for provider in self.providers:
                t0 = time.monotonic()
                fetched = new_count = dup_count = errors = 0
                try:
                    posts = await provider.fetch_for_symbols(
                        symbols, limit_per_symbol=8, hours_back=hours_back,
                    )
                    for raw_post in posts:
                        fetched += 1
                        enriched = self._enrich(dict(raw_post))
                        try:
                            await raw_repo.store(
                                provider.config.name, "social_post",
                                enriched.get("url", "unknown"),
                                {"text": enriched.get("text", "")[:200], "url": enriched.get("url")},
                            )
                            _, created = await social_repo.upsert(enriched)
                            if created:
                                new_count += 1
                            else:
                                dup_count += 1
                        except Exception as exc:  # noqa: BLE001
                            errors += 1
                            logger.warning("social_upsert_failed", error=str(exc))
                    ms = int((time.monotonic() - t0) * 1000)
                    logger.info(
                        "social_collected",
                        provider=provider.config.name,
                        fetched=fetched, new=new_count, dupes=dup_count, errors=errors, ms=ms,
                    )
                    summary[provider.config.name] = {
                        "posts_fetched": fetched,
                        "new_posts": new_count,
                        "duplicate_posts": dup_count,
                        "errors": errors,
                    }
                except Exception as exc:  # noqa: BLE001
                    ms = int((time.monotonic() - t0) * 1000)
                    logger.error(
                        "social_provider_failed",
                        provider=provider.config.name, error=str(exc), ms=ms,
                    )
                    summary[provider.config.name] = {
                        "posts_fetched": 0, "new_posts": 0,
                        "duplicate_posts": 0, "errors": 1,
                    }
            await db.commit()
        return summary
