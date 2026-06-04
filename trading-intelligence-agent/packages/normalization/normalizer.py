"""Data normalization and deduplication utilities."""
from __future__ import annotations

import json
import hashlib
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import xxhash

from packages.social_intel.ticker_extractor import TickerExtractor
from packages.social_intel.sentiment import SentimentScorer

_extractor = TickerExtractor()
_sentiment = SentimentScorer()


def compute_content_hash(text: str | None, url: str | None = None) -> str:
    combined = (text or "") + (url or "")
    return xxhash.xxh64(combined.encode()).hexdigest()


def compute_payload_hash(payload: dict | str) -> str:
    if isinstance(payload, dict):
        payload = json.dumps(payload, sort_keys=True, default=str)
    return xxhash.xxh64(payload.encode()).hexdigest()


def _parse_datetime(raw: Any) -> datetime:
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
    if isinstance(raw, (int, float)):
        return datetime.fromtimestamp(raw, tz=timezone.utc)
    if isinstance(raw, str):
        raw = raw.strip()
        for fmt in (
            None,  # fromisoformat
            "%a, %d %b %Y %H:%M:%S %z",  # RFC2822
            "%a, %d %b %Y %H:%M:%S %Z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ):
            try:
                if fmt is None:
                    dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                else:
                    dt = datetime.strptime(raw, fmt)
                return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                continue
        try:
            dt = parsedate_to_datetime(raw)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            pass
    return datetime.now(tz=timezone.utc)


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


class MarketPriceNormalizer:
    def normalize(
        self, raw: dict[str, Any], source: str, symbol: str, asset_id: int,
    ) -> dict[str, Any]:
        ts = _parse_datetime(raw.get("timestamp") or raw.get("t") or raw.get("date"))
        return {
            "asset_id": asset_id,
            "symbol": symbol,
            "timestamp": ts.isoformat(),
            "open": float(raw.get("open") or raw.get("o") or 0),
            "high": float(raw.get("high") or raw.get("h") or 0),
            "low": float(raw.get("low") or raw.get("l") or 0),
            "close": float(raw.get("close") or raw.get("c") or 0),
            "volume": float(raw.get("volume") or raw.get("v") or 0),
            "source": source,
            "interval": str(raw.get("interval") or "1d"),
        }

    def normalize_batch(
        self, raws: list[dict[str, Any]], source: str, symbol: str, asset_id: int,
    ) -> list[dict[str, Any]]:
        return [self.normalize(r, source, symbol, asset_id) for r in raws]


class NewsNormalizer:
    def normalize(self, raw: dict[str, Any], provider_name: str) -> dict[str, Any]:
        title = str(raw.get("title") or "")
        url = str(raw.get("url") or "")
        raw_text = str(raw.get("raw_text") or raw.get("content") or raw.get("body") or "")[:5000]
        tickers = raw.get("tickers_mentioned") or _extractor.extract(title + " " + raw_text)
        return {
            "source": str(raw.get("source") or provider_name),
            "author": raw.get("author"),
            "title": title,
            "url": url,
            "published_at": _parse_datetime(raw.get("published_at") or raw.get("pubDate")).isoformat(),
            "fetched_at": _now().isoformat(),
            "summary": raw.get("summary") or raw.get("description"),
            "content_hash": compute_content_hash(title, url),
            "tickers_mentioned": list(tickers),
            "assets_mentioned": list(tickers),
            "raw_text": raw_text or None,
            "credibility_score": float(raw.get("credibility_score") or 0.5),
        }


class SocialPostNormalizer:
    def normalize(
        self, raw: dict[str, Any], platform: str, community: str | None,
    ) -> dict[str, Any]:
        text = str(raw.get("text") or raw.get("body") or raw.get("selftext") or "")
        author_id = str(raw.get("author") or raw.get("author_id") or raw.get("user") or "unknown")
        author_hash = xxhash.xxh64(author_id.encode()).hexdigest()[:12]
        tickers = raw.get("tickers_mentioned") or _extractor.extract(text)
        sentiment_score = float(raw.get("sentiment_score") or _sentiment.score_text(text))
        spam_score = float(raw.get("toxicity_or_spam_score") or _sentiment.score_spam(text))
        return {
            "platform": platform,
            "source_community": community or raw.get("subreddit") or raw.get("community"),
            "author_hash": author_hash,
            "url": raw.get("url") or raw.get("permalink"),
            "posted_at": _parse_datetime(raw.get("posted_at") or raw.get("created_utc") or raw.get("timestamp")).isoformat(),
            "fetched_at": _now().isoformat(),
            "text": text,
            "tickers_mentioned": list(tickers),
            "assets_mentioned": list(tickers),
            "engagement_score": float(raw.get("engagement_score") or 0.0),
            "credibility_score": float(raw.get("credibility_score") or 0.5),
            "sentiment_score": sentiment_score,
            "toxicity_or_spam_score": spam_score,
        }


class Deduplicator:
    def __init__(self) -> None:
        self._seen: set[str] = set()

    def is_duplicate(self, hash_val: str) -> bool:
        return hash_val in self._seen

    def mark_seen(self, hash_val: str) -> None:
        self._seen.add(hash_val)

    async def check_db_exists(self, db: Any, hash_val: str, table: str) -> bool:
        from sqlalchemy import text as sql_text
        if table == "raw_payloads":
            result = await db.execute(
                sql_text("SELECT 1 FROM raw_payloads WHERE payload_hash = :h LIMIT 1"),
                {"h": hash_val},
            )
        elif table == "news_articles":
            result = await db.execute(
                sql_text("SELECT 1 FROM news_articles WHERE content_hash = :h LIMIT 1"),
                {"h": hash_val},
            )
        else:
            return False
        return result.scalar() is not None
