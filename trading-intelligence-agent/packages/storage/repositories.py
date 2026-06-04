"""Firestore repositories — CRUD operations for all collections.

Collection layout:
  assets/{symbol}
  watchlist/{symbol}
  market_prices/{symbol}_{timestamp_iso}_{interval}
  news_articles/{content_hash}
  social_posts/{auto_id}
  macro_indicators/{name}_{timestamp_iso}
  filing_documents/{accession_number}
  signals/{auto_id}
  raw_payloads/{payload_hash}
  daily_briefings/{date_str}
  asset_research_reports/{asset_id}_{date_str}
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

import xxhash
import structlog

logger = structlog.get_logger()


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _hash_payload(data: dict | str) -> str:
    if isinstance(data, dict):
        data = json.dumps(data, sort_keys=True, default=str)
    return xxhash.xxh64(data.encode()).hexdigest()


def _to_dt(val: Any) -> datetime | None:
    """Coerce Firestore Timestamp, ISO string, or datetime to datetime."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val if val.tzinfo else val.replace(tzinfo=timezone.utc)
    # Firestore DatetimeWithNanoseconds has .timestamp_pb()
    if hasattr(val, "ToDatetime"):
        return val.ToDatetime().replace(tzinfo=timezone.utc)
    if isinstance(val, str):
        try:
            dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            return _now()
    return _now()


# ---------------------------------------------------------------------------
# Tiny data classes that mirror the ORM rows that routes/services expect
# ---------------------------------------------------------------------------

class _Row:
    """Generic attribute container — mimics SQLAlchemy row interface."""
    def __init__(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)
    def __repr__(self) -> str:
        return f"<Row {self.__dict__}>"


def _asset_row(data: dict, doc_id: str) -> _Row:
    return _Row(
        id=data.get("id") or doc_id,
        symbol=data.get("symbol", doc_id),
        name=data.get("name", ""),
        asset_class=data.get("asset_class", "stock"),
        exchange=data.get("exchange"),
        currency=data.get("currency", "USD"),
        sector=data.get("sector"),
        industry=data.get("industry"),
        metadata_json=data.get("metadata_json", {}),
        is_active=data.get("is_active", True),
        created_at=_to_dt(data.get("created_at")),
        updated_at=_to_dt(data.get("updated_at")),
    )


def _price_row(data: dict, doc_id: str) -> _Row:
    return _Row(
        id=doc_id,
        asset_id=data.get("asset_id"),
        timestamp=_to_dt(data.get("timestamp")),
        open=data.get("open"),
        high=data.get("high"),
        low=data.get("low"),
        close=data.get("close", 0.0),
        volume=data.get("volume"),
        source=data.get("source", ""),
        interval=data.get("interval", "1d"),
    )


def _news_row(data: dict, doc_id: str) -> _Row:
    return _Row(
        id=data.get("id") or doc_id,
        source=data.get("source", ""),
        author=data.get("author"),
        title=data.get("title", ""),
        url=data.get("url", ""),
        published_at=_to_dt(data.get("published_at")),
        fetched_at=_to_dt(data.get("fetched_at")),
        summary=data.get("summary"),
        content_hash=data.get("content_hash", doc_id),
        tickers_mentioned=data.get("tickers_mentioned") or [],
        assets_mentioned=data.get("assets_mentioned") or [],
        raw_text=data.get("raw_text"),
        credibility_score=float(data.get("credibility_score", 0.5)),
    )


def _social_row(data: dict, doc_id: str) -> _Row:
    return _Row(
        id=data.get("id") or doc_id,
        platform=data.get("platform", ""),
        source_community=data.get("source_community"),
        author_hash=data.get("author_hash", ""),
        url=data.get("url"),
        posted_at=_to_dt(data.get("posted_at")),
        fetched_at=_to_dt(data.get("fetched_at")),
        text=data.get("text", ""),
        tickers_mentioned=data.get("tickers_mentioned") or [],
        assets_mentioned=data.get("assets_mentioned") or [],
        engagement_score=float(data.get("engagement_score", 0.0)),
        credibility_score=float(data.get("credibility_score", 0.5)),
        sentiment_score=float(data.get("sentiment_score", 0.0)),
        toxicity_or_spam_score=float(data.get("toxicity_or_spam_score", 0.0)),
    )


def _macro_row(data: dict, doc_id: str) -> _Row:
    return _Row(
        id=data.get("id") or doc_id,
        name=data.get("name", ""),
        timestamp=_to_dt(data.get("timestamp")),
        value=float(data.get("value", 0.0)),
        unit=data.get("unit", ""),
        source=data.get("source", ""),
        category=data.get("category", ""),
    )


def _signal_row(data: dict, doc_id: str) -> _Row:
    return _Row(
        id=data.get("id") or doc_id,
        asset_id=data.get("asset_id"),
        timestamp=_to_dt(data.get("timestamp")),
        horizon=data.get("horizon", "swing"),
        signal_type=data.get("signal_type", "composite"),
        direction=data.get("direction", "neutral"),
        score=float(data.get("score", 0.0)),
        confidence=float(data.get("confidence", 0.5)),
        evidence_ids=data.get("evidence_ids") or [],
        reasoning=data.get("reasoning", ""),
        counterarguments=data.get("counterarguments") or [],
        risk_flags=data.get("risk_flags") or [],
        created_by=data.get("created_by", "system"),
        version=data.get("version", "1.0"),
        created_at=_to_dt(data.get("created_at")),
    )


def _briefing_row(data: dict, doc_id: str) -> _Row:
    return _Row(
        id=data.get("id") or doc_id,
        date=data.get("date", doc_id),
        market_regime_summary=data.get("market_regime_summary", ""),
        macro_summary=data.get("macro_summary", ""),
        equity_summary=data.get("equity_summary", ""),
        etf_summary=data.get("etf_summary", ""),
        bond_summary=data.get("bond_summary", ""),
        crypto_summary=data.get("crypto_summary", ""),
        top_opportunities=data.get("top_opportunities") or [],
        top_risks=data.get("top_risks") or [],
        unusual_social_activity=data.get("unusual_social_activity") or [],
        major_news_events=data.get("major_news_events") or [],
        watchlist_changes=data.get("watchlist_changes") or [],
        evidence_ids=data.get("evidence_ids") or [],
        disclaimer=data.get("disclaimer", ""),
        created_at=_to_dt(data.get("created_at")),
    )


# ---------------------------------------------------------------------------
# Repository classes
# ---------------------------------------------------------------------------

class AssetRepository:
    def __init__(self, db: Any) -> None:
        self.db = db
        self._col = db.collection("assets")
        self._wl = db.collection("watchlist")

    async def get_by_id(self, asset_id: str) -> _Row | None:
        doc = await self._col.document(str(asset_id)).get()
        return _asset_row(doc.to_dict() or {}, doc.id) if doc.exists else None

    async def get_by_symbol(self, symbol: str) -> _Row | None:
        doc = await self._col.document(symbol.upper()).get()
        return _asset_row(doc.to_dict() or {}, doc.id) if doc.exists else None

    async def get_all(
        self, asset_class: str | None = None, is_active: bool = True
    ) -> list[_Row]:
        q = self._col.where("is_active", "==", is_active)
        if asset_class:
            q = q.where("asset_class", "==", asset_class)
        return [_asset_row(d.to_dict() or {}, d.id) async for d in q.stream()]

    async def create(self, asset: Any) -> _Row:
        return await self.upsert(asset)

    async def upsert(self, asset: Any) -> _Row:
        sym = asset.symbol.upper()
        data = {
            "id": sym,
            "symbol": sym,
            "name": asset.name,
            "asset_class": asset.asset_class.value if hasattr(asset.asset_class, "value") else str(asset.asset_class),
            "exchange": asset.exchange,
            "currency": getattr(asset, "currency", "USD"),
            "sector": getattr(asset, "sector", None),
            "industry": getattr(asset, "industry", None),
            "is_active": getattr(asset, "is_active", True),
            "created_at": _now().isoformat(),
            "updated_at": _now().isoformat(),
        }
        await self._col.document(sym).set(data, merge=True)
        return _asset_row(data, sym)

    async def get_watchlist(self) -> list[_Row]:
        rows: list[_Row] = []
        async for wl_doc in self._wl.stream():
            sym = wl_doc.id
            asset_doc = await self._col.document(sym).get()
            if asset_doc.exists:
                rows.append(_asset_row(asset_doc.to_dict() or {}, sym))
        return rows

    async def add_to_watchlist(self, asset_id: str, notes: str = "") -> _Row:
        await self._wl.document(str(asset_id)).set(
            {"asset_id": str(asset_id), "notes": notes, "added_at": _now().isoformat()},
            merge=True,
        )
        return _Row(asset_id=str(asset_id), notes=notes, added_at=_now())

    async def remove_from_watchlist(self, asset_id: str) -> bool:
        doc = await self._wl.document(str(asset_id)).get()
        if doc.exists:
            await self._wl.document(str(asset_id)).delete()
            return True
        return False


class MarketPriceRepository:
    def __init__(self, db: Any) -> None:
        self.db = db
        self._col = db.collection("market_prices")

    def _doc_id(self, symbol: str, ts: str, interval: str) -> str:
        safe_ts = ts.replace(":", "-").replace("+", "_")
        return f"{symbol}_{safe_ts}_{interval}"

    async def bulk_upsert(self, prices: list[dict[str, Any]]) -> int:
        if not prices:
            return 0
        batch = self.db.batch()
        count = 0
        for p in prices:
            symbol = p.get("symbol", "")
            ts_raw = p.get("timestamp", "")
            interval = p.get("interval", "1d")
            if isinstance(ts_raw, datetime):
                ts_str = ts_raw.isoformat()
            else:
                ts_str = str(ts_raw)
            doc_id = self._doc_id(symbol, ts_str, interval)
            ref = self._col.document(doc_id)
            data = {
                "asset_id": symbol,
                "symbol": symbol,
                "timestamp": ts_str,
                "open": p.get("open"),
                "high": p.get("high"),
                "low": p.get("low"),
                "close": float(p.get("close", 0)),
                "volume": p.get("volume"),
                "source": p.get("source", ""),
                "interval": interval,
            }
            batch.set(ref, data, merge=False)
            count += 1
            if count % 400 == 0:  # Firestore batch limit is 500
                await batch.commit()
                batch = self.db.batch()
        if count % 400 != 0:
            await batch.commit()
        return count

    async def get_latest(self, asset_id: Any) -> _Row | None:
        sym = str(asset_id)
        docs = await (
            self._col
            .where("symbol", "==", sym)
            .order_by("timestamp", direction="DESCENDING")
            .limit(1)
            .get()
        )
        if not docs:
            return None
        d = docs[0]
        return _price_row(d.to_dict() or {}, d.id)

    async def get_range(
        self,
        asset_id: Any,
        start: datetime,
        end: datetime,
        interval: str = "1d",
    ) -> list[_Row]:
        sym = str(asset_id)
        start_str = start.isoformat()
        end_str = end.isoformat()
        docs = await (
            self._col
            .where("symbol", "==", sym)
            .where("interval", "==", interval)
            .where("timestamp", ">=", start_str)
            .where("timestamp", "<=", end_str)
            .order_by("timestamp")
            .get()
        )
        return [_price_row(d.to_dict() or {}, d.id) for d in docs]


class NewsRepository:
    def __init__(self, db: Any) -> None:
        self.db = db
        self._col = db.collection("news_articles")

    async def upsert_by_hash(self, article: dict[str, Any]) -> tuple[_Row, bool]:
        content_hash = article.get("content_hash", "")
        if not content_hash:
            content_hash = xxhash.xxh64(
                (article.get("title", "") + article.get("url", "")).encode()
            ).hexdigest()

        doc = await self._col.document(content_hash).get()
        if doc.exists:
            return _news_row(doc.to_dict() or {}, content_hash), False

        data = {
            "id": content_hash,
            **{k: v for k, v in article.items()},
            "fetched_at": _now().isoformat(),
        }
        await self._col.document(content_hash).set(data)
        return _news_row(data, content_hash), True

    async def get_by_symbol(
        self, symbol: str, limit: int = 50, hours_back: int = 72
    ) -> list[_Row]:
        cutoff = (_now() - timedelta(hours=hours_back)).isoformat()
        docs = await (
            self._col
            .where("tickers_mentioned", "array_contains", symbol.upper())
            .where("fetched_at", ">=", cutoff)
            .order_by("fetched_at", direction="DESCENDING")
            .limit(limit)
            .get()
        )
        return [_news_row(d.to_dict() or {}, d.id) for d in docs]

    async def get_recent(self, limit: int = 100, hours_back: int = 24) -> list[_Row]:
        cutoff = (_now() - timedelta(hours=hours_back)).isoformat()
        docs = await (
            self._col
            .where("fetched_at", ">=", cutoff)
            .order_by("fetched_at", direction="DESCENDING")
            .limit(limit)
            .get()
        )
        return [_news_row(d.to_dict() or {}, d.id) for d in docs]


class SocialPostRepository:
    def __init__(self, db: Any) -> None:
        self.db = db
        self._col = db.collection("social_posts")

    async def upsert(self, post: dict[str, Any]) -> tuple[_Row, bool]:
        url = post.get("url") or ""
        if url:
            # Check by URL
            docs = await self._col.where("url", "==", url).limit(1).get()
            if docs:
                d = docs[0]
                return _social_row(d.to_dict() or {}, d.id), False

        ref = self._col.document()
        data = {"id": ref.id, **post, "fetched_at": _now().isoformat()}
        await ref.set(data)
        return _social_row(data, ref.id), True

    async def get_by_symbol(
        self, symbol: str, limit: int = 50, hours_back: int = 48
    ) -> list[_Row]:
        cutoff = (_now() - timedelta(hours=hours_back)).isoformat()
        docs = await (
            self._col
            .where("tickers_mentioned", "array_contains", symbol.upper())
            .where("fetched_at", ">=", cutoff)
            .order_by("fetched_at", direction="DESCENDING")
            .limit(limit)
            .get()
        )
        return [_social_row(d.to_dict() or {}, d.id) for d in docs]

    async def get_trending(self, limit: int = 20, hours_back: int = 6) -> list[_Row]:
        cutoff = (_now() - timedelta(hours=hours_back)).isoformat()
        docs = await (
            self._col
            .where("fetched_at", ">=", cutoff)
            .order_by("engagement_score", direction="DESCENDING")
            .limit(limit)
            .get()
        )
        return [_social_row(d.to_dict() or {}, d.id) for d in docs]


class MacroRepository:
    def __init__(self, db: Any) -> None:
        self.db = db
        self._col = db.collection("macro_indicators")

    def _doc_id(self, name: str, ts: str) -> str:
        safe_ts = ts.replace(":", "-").replace("+", "_")
        return f"{name}_{safe_ts}"

    async def upsert(self, series_id: str, observations: list[dict[str, Any]]) -> int:
        batch = self.db.batch()
        count = 0
        for obs in observations:
            ts_raw = obs.get("observation_date", obs.get("timestamp", ""))
            if isinstance(ts_raw, datetime):
                ts_str = ts_raw.isoformat()
            else:
                ts_str = str(ts_raw)
            doc_id = self._doc_id(series_id, ts_str)
            data = {
                "name": series_id,
                "timestamp": ts_str,
                "value": float(obs.get("value", 0.0)),
                "unit": str(obs.get("unit", "")),
                "source": str(obs.get("source", "")),
                "category": str(obs.get("category", "")),
            }
            batch.set(self._col.document(doc_id), data, merge=False)
            count += 1
        await batch.commit()
        return count

    async def get_latest(self, name: str, limit: int = 1) -> list[dict[str, Any]]:
        docs = await (
            self._col
            .where("name", "==", name)
            .order_by("timestamp", direction="DESCENDING")
            .limit(limit)
            .get()
        )
        return [d.to_dict() or {} for d in docs]

    async def get_latest_by_name(self, name: str) -> _Row | None:
        rows = await self.get_latest(name, limit=1)
        if not rows:
            return None
        d = rows[0]
        return _macro_row(d, f"{name}_latest")

    async def get_series(self, name: str, limit: int = 100) -> list[_Row]:
        docs = await (
            self._col
            .where("name", "==", name)
            .order_by("timestamp", direction="DESCENDING")
            .limit(limit)
            .get()
        )
        return [_macro_row(d.to_dict() or {}, d.id) for d in docs]

    async def get_all_latest(self) -> list[_Row]:
        series_ids = [
            "fed_funds_rate", "cpi_yoy", "gdp_growth_qoq", "unemployment_rate",
            "10y_treasury_yield", "2y_treasury_yield", "vix", "dxy",
        ]
        rows: list[_Row] = []
        for name in series_ids:
            latest = await self.get_latest(name, limit=1)
            if latest:
                rows.append(_macro_row(latest[0], f"{name}_latest"))
        return rows


class RawPayloadRepository:
    def __init__(self, db: Any) -> None:
        self.db = db
        self._col = db.collection("raw_payloads")

    async def store(
        self,
        source: str,
        payload_type: str,
        symbol: str,
        data: dict[str, Any],
    ) -> _Row:
        payload_hash = _hash_payload(data)
        doc = await self._col.document(payload_hash).get()
        if doc.exists:
            return _Row(id=payload_hash, payload_hash=payload_hash, parse_status="success")

        row_data = {
            "id": payload_hash,
            "source": source,
            "provider": source,
            "endpoint": f"{payload_type}/{symbol}",
            "fetched_at": _now().isoformat(),
            "payload_hash": payload_hash,
            "payload_json": data,
            "parse_status": "success",
        }
        await self._col.document(payload_hash).set(row_data)
        return _Row(**row_data)

    async def exists_by_hash(self, hash_val: str) -> bool:
        doc = await self._col.document(hash_val).get()
        return doc.exists

    async def get_by_id(self, payload_id: str) -> _Row | None:
        doc = await self._col.document(str(payload_id)).get()
        if not doc.exists:
            return None
        d = doc.to_dict() or {}
        return _Row(**d)

    async def update_parse_status(
        self, payload_id: str, status: Any, error: str | None = None
    ) -> None:
        await self._col.document(str(payload_id)).update({
            "parse_status": status.value if hasattr(status, "value") else str(status),
            "error_message": error,
        })


class SignalRepository:
    def __init__(self, db: Any) -> None:
        self.db = db
        self._col = db.collection("signals")

    async def create(self, signal: dict[str, Any]) -> _Row:
        ref = self._col.document()
        data = {
            "id": ref.id,
            "created_at": _now().isoformat(),
            **signal,
        }
        if isinstance(data.get("timestamp"), datetime):
            data["timestamp"] = data["timestamp"].isoformat()
        await ref.set(data)
        return _signal_row(data, ref.id)

    async def get_by_asset(self, asset_id: Any, limit: int = 20) -> list[_Row]:
        docs = await (
            self._col
            .where("asset_id", "==", int(asset_id) if str(asset_id).isdigit() else str(asset_id))
            .order_by("created_at", direction="DESCENDING")
            .limit(limit)
            .get()
        )
        return [_signal_row(d.to_dict() or {}, d.id) for d in docs]

    async def get_latest_by_asset(self, asset_id: Any) -> _Row | None:
        rows = await self.get_by_asset(asset_id, limit=1)
        return rows[0] if rows else None

    async def get_recent(self, limit: int = 50) -> list[_Row]:
        docs = await (
            self._col
            .order_by("created_at", direction="DESCENDING")
            .limit(limit)
            .get()
        )
        return [_signal_row(d.to_dict() or {}, d.id) for d in docs]

    async def get_by_id(self, signal_id: str) -> _Row | None:
        doc = await self._col.document(str(signal_id)).get()
        return _signal_row(doc.to_dict() or {}, doc.id) if doc.exists else None


class DailyBriefingRepository:
    def __init__(self, db: Any) -> None:
        self.db = db
        self._col = db.collection("daily_briefings")

    async def create(self, briefing: dict[str, Any]) -> _Row:
        date_val = briefing.get("date", "")
        if hasattr(date_val, "isoformat"):
            date_str = date_val.isoformat()
        else:
            date_str = str(date_val)

        existing = await self.get_by_date(date_str)
        if existing:
            return existing

        data = {
            "id": date_str,
            "created_at": _now().isoformat(),
            **{k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in briefing.items()},
        }
        await self._col.document(date_str).set(data)
        return _briefing_row(data, date_str)

    async def get_latest(self) -> _Row | None:
        docs = await (
            self._col
            .order_by("date", direction="DESCENDING")
            .limit(1)
            .get()
        )
        if not docs:
            return None
        d = docs[0]
        return _briefing_row(d.to_dict() or {}, d.id)

    async def get_by_date(self, date_str: str) -> _Row | None:
        doc = await self._col.document(date_str).get()
        return _briefing_row(doc.to_dict() or {}, doc.id) if doc.exists else None
