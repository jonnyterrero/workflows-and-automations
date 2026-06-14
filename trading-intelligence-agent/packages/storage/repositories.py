"""SQLAlchemy repositories for the trading intelligence agent."""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from typing import Any

import structlog
import xxhash
from sqlalchemy import delete, desc, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from packages.core_models.db_tables import (
    AssetTable,
    DailyBriefingTable,
    MacroIndicatorTable,
    MarketPriceTable,
    NewsArticleTable,
    PortfolioPolicyRuleTable,
    PortfolioPositionTable,
    PortfolioProfileTable,
    RawPayloadTable,
    SignalTable,
    SocialPostTable,
    WatchlistTable,
)
from packages.policy.models import PolicyRule, PortfolioPosition, PortfolioProfile

logger = structlog.get_logger()


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _hash_payload(data: dict[str, Any] | str) -> str:
    if isinstance(data, dict):
        data = json.dumps(data, sort_keys=True, default=str)
    return xxhash.xxh64(data.encode()).hexdigest()


def _to_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time(), tzinfo=timezone.utc)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def _json_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return list(value)


async def _commit_refresh(db: AsyncSession, row: Any) -> Any:
    await db.commit()
    await db.refresh(row)
    return row


class _BaseRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _resolve_asset(self, asset_id: Any) -> AssetTable | None:
        if isinstance(asset_id, int) or str(asset_id).isdigit():
            return await self.db.get(AssetTable, int(asset_id))
        result = await self.db.execute(
            select(AssetTable).where(AssetTable.symbol == str(asset_id).upper())
        )
        return result.scalar_one_or_none()

    def _insert_ignore_stmt(self, model: Any, rows: list[dict[str, Any]], conflict_cols: list[str]) -> Any:
        dialect_name = self.db.bind.dialect.name if self.db.bind else "sqlite"
        if dialect_name == "postgresql":
            return pg_insert(model).values(rows).on_conflict_do_nothing(index_elements=conflict_cols)
        if dialect_name == "sqlite":
            return sqlite_insert(model).values(rows).on_conflict_do_nothing(index_elements=conflict_cols)
        raise RuntimeError(f"Unsupported SQL dialect for bulk upsert: {dialect_name}")


class AssetRepository(_BaseRepository):
    async def get_by_id(self, asset_id: Any) -> AssetTable | None:
        return await self._resolve_asset(asset_id)

    async def get_by_symbol(self, symbol: str) -> AssetTable | None:
        result = await self.db.execute(select(AssetTable).where(AssetTable.symbol == symbol.upper()))
        return result.scalar_one_or_none()

    async def get_all(self, asset_class: str | None = None, is_active: bool = True) -> list[AssetTable]:
        stmt = select(AssetTable).where(AssetTable.is_active == is_active).order_by(AssetTable.symbol)
        if asset_class:
            stmt = stmt.where(AssetTable.asset_class == asset_class)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, asset: Any) -> AssetTable:
        return await self.upsert(asset)

    async def upsert(self, asset: Any) -> AssetTable:
        symbol = str(asset.symbol).upper()
        existing = await self.get_by_symbol(symbol)
        data = {
            "symbol": symbol,
            "name": asset.name,
            "asset_class": asset.asset_class.value if hasattr(asset.asset_class, "value") else str(asset.asset_class),
            "exchange": getattr(asset, "exchange", None),
            "currency": getattr(asset, "currency", "USD"),
            "sector": getattr(asset, "sector", None),
            "industry": getattr(asset, "industry", None),
            "theme_tags": getattr(asset, "theme_tags", []),
            "metadata_json": getattr(asset, "metadata", None) or getattr(asset, "metadata_json", None),
            "is_active": getattr(asset, "is_active", True),
        }
        if existing:
            for key, value in data.items():
                setattr(existing, key, value)
            return await _commit_refresh(self.db, existing)

        row = AssetTable(**data)
        self.db.add(row)
        return await _commit_refresh(self.db, row)

    async def get_watchlist(self) -> list[AssetTable]:
        stmt = (
            select(AssetTable)
            .join(WatchlistTable, WatchlistTable.asset_id == AssetTable.id)
            .order_by(AssetTable.symbol)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def add_to_watchlist(self, asset_id: Any, notes: str = "") -> WatchlistTable:
        resolved_id = int(asset_id)
        result = await self.db.execute(
            select(WatchlistTable).where(WatchlistTable.asset_id == resolved_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.notes = notes
            return await _commit_refresh(self.db, existing)

        row = WatchlistTable(asset_id=resolved_id, notes=notes)
        self.db.add(row)
        return await _commit_refresh(self.db, row)

    async def remove_from_watchlist(self, asset_id: Any) -> bool:
        result = await self.db.execute(
            select(WatchlistTable).where(WatchlistTable.asset_id == int(asset_id))
        )
        row = result.scalar_one_or_none()
        if row is None:
            return False
        await self.db.delete(row)
        await self.db.commit()
        return True


class MarketPriceRepository(_BaseRepository):
    async def bulk_upsert(self, prices: list[dict[str, Any]]) -> int:
        if not prices:
            return 0

        symbols = {str(price.get("symbol", "")).upper() for price in prices if price.get("symbol")}
        asset_rows = {}
        if symbols:
            result = await self.db.execute(select(AssetTable).where(AssetTable.symbol.in_(symbols)))
            asset_rows = {row.symbol: row.id for row in result.scalars().all()}

        rows: list[dict[str, Any]] = []
        for price in prices:
            symbol = str(price.get("symbol", "")).upper()
            asset_id = price.get("asset_id") or asset_rows.get(symbol)
            if asset_id is None:
                continue
            timestamp = _to_datetime(price.get("timestamp"))
            if timestamp is None:
                continue
            rows.append(
                {
                    "asset_id": int(asset_id),
                    "symbol": symbol or None,
                    "timestamp": timestamp,
                    "open": price.get("open"),
                    "high": price.get("high"),
                    "low": price.get("low"),
                    "close": float(price.get("close", 0.0)),
                    "adjusted_close": price.get("adjusted_close"),
                    "volume": price.get("volume"),
                    "source": str(price.get("source", "seed")),
                    "interval": str(price.get("interval", "1d")),
                }
            )

        if not rows:
            return 0

        await self.db.execute(
            self._insert_ignore_stmt(
                MarketPriceTable,
                rows,
                ["asset_id", "timestamp", "interval", "source"],
            )
        )
        await self.db.commit()
        return len(rows)

    async def get_latest(self, asset_id: Any) -> MarketPriceTable | None:
        asset = await self._resolve_asset(asset_id)
        if asset is None:
            return None
        result = await self.db.execute(
            select(MarketPriceTable)
            .where(MarketPriceTable.asset_id == asset.id)
            .order_by(desc(MarketPriceTable.timestamp))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_range(
        self,
        asset_id: Any,
        start: datetime,
        end: datetime,
        interval: str = "1d",
    ) -> list[MarketPriceTable]:
        asset = await self._resolve_asset(asset_id)
        if asset is None:
            return []
        result = await self.db.execute(
            select(MarketPriceTable)
            .where(MarketPriceTable.asset_id == asset.id)
            .where(MarketPriceTable.interval == interval)
            .where(MarketPriceTable.timestamp >= start)
            .where(MarketPriceTable.timestamp <= end)
            .order_by(MarketPriceTable.timestamp)
        )
        return list(result.scalars().all())


class NewsRepository(_BaseRepository):
    async def upsert_by_hash(self, article: dict[str, Any]) -> tuple[NewsArticleTable, bool]:
        content_hash = str(article.get("content_hash") or _hash_payload(article))
        result = await self.db.execute(
            select(NewsArticleTable).where(NewsArticleTable.content_hash == content_hash)
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            return existing, False

        row = NewsArticleTable(
            source=str(article.get("source", "")),
            author=article.get("author"),
            title=str(article.get("title", "")),
            url=str(article.get("url", "")),
            published_at=_to_datetime(article.get("published_at")) or _now(),
            fetched_at=_to_datetime(article.get("fetched_at")) or _now(),
            summary=article.get("summary"),
            content_hash=content_hash,
            tickers_mentioned=_json_list(article.get("tickers_mentioned")),
            assets_mentioned=_json_list(article.get("assets_mentioned")),
            raw_text=article.get("raw_text"),
            credibility_score=float(article.get("credibility_score", 0.5)),
        )
        self.db.add(row)
        return await _commit_refresh(self.db, row), True

    async def get_by_symbol(self, symbol: str, limit: int = 50, hours_back: int = 72) -> list[NewsArticleTable]:
        cutoff = _now() - timedelta(hours=hours_back)
        result = await self.db.execute(
            select(NewsArticleTable)
            .where(NewsArticleTable.fetched_at >= cutoff)
            .order_by(desc(NewsArticleTable.fetched_at))
            .limit(max(limit * 5, limit))
        )
        rows = [
            row for row in result.scalars().all()
            if symbol.upper() in (row.tickers_mentioned or [])
        ]
        return rows[:limit]

    async def get_recent(self, limit: int = 100, hours_back: int = 24) -> list[NewsArticleTable]:
        cutoff = _now() - timedelta(hours=hours_back)
        result = await self.db.execute(
            select(NewsArticleTable)
            .where(NewsArticleTable.fetched_at >= cutoff)
            .order_by(desc(NewsArticleTable.fetched_at))
            .limit(limit)
        )
        return list(result.scalars().all())


class SocialPostRepository(_BaseRepository):
    async def upsert(self, post: dict[str, Any]) -> tuple[SocialPostTable, bool]:
        url = post.get("url")
        if url:
            result = await self.db.execute(select(SocialPostTable).where(SocialPostTable.url == str(url)))
            existing = result.scalar_one_or_none()
            if existing is not None:
                return existing, False

        row = SocialPostTable(
            platform=str(post.get("platform", "")),
            source_community=post.get("source_community"),
            author_hash=str(post.get("author_hash", "")),
            url=str(url) if url else None,
            posted_at=_to_datetime(post.get("posted_at")) or _now(),
            fetched_at=_to_datetime(post.get("fetched_at")) or _now(),
            text=str(post.get("text", "")),
            tickers_mentioned=_json_list(post.get("tickers_mentioned")),
            assets_mentioned=_json_list(post.get("assets_mentioned")),
            engagement_score=float(post.get("engagement_score", 0.0)),
            credibility_score=float(post.get("credibility_score", 0.5)),
            sentiment_score=float(post.get("sentiment_score", 0.0)),
            toxicity_or_spam_score=float(post.get("toxicity_or_spam_score", 0.0)),
        )
        self.db.add(row)
        return await _commit_refresh(self.db, row), True

    async def get_by_symbol(self, symbol: str, limit: int = 50, hours_back: int = 48) -> list[SocialPostTable]:
        cutoff = _now() - timedelta(hours=hours_back)
        result = await self.db.execute(
            select(SocialPostTable)
            .where(SocialPostTable.fetched_at >= cutoff)
            .order_by(desc(SocialPostTable.fetched_at))
            .limit(max(limit * 5, limit))
        )
        rows = [
            row for row in result.scalars().all()
            if symbol.upper() in (row.tickers_mentioned or [])
        ]
        return rows[:limit]

    async def get_trending(self, limit: int = 20, hours_back: int = 6) -> list[SocialPostTable]:
        cutoff = _now() - timedelta(hours=hours_back)
        result = await self.db.execute(
            select(SocialPostTable)
            .where(SocialPostTable.fetched_at >= cutoff)
            .order_by(desc(SocialPostTable.engagement_score))
            .limit(limit)
        )
        return list(result.scalars().all())


class MacroRepository(_BaseRepository):
    async def upsert(self, series_id: str, observations: list[dict[str, Any]]) -> int:
        rows: list[dict[str, Any]] = []
        for observation in observations:
            timestamp = _to_datetime(
                observation.get("observation_date") or observation.get("timestamp")
            )
            if timestamp is None:
                continue
            rows.append(
                {
                    "name": series_id,
                    "timestamp": timestamp,
                    "value": float(observation.get("value", 0.0)),
                    "unit": str(observation.get("unit", "")),
                    "source": str(observation.get("source", "seed")),
                    "category": str(observation.get("category", "")),
                }
            )
        if not rows:
            return 0
        await self.db.execute(
            self._insert_ignore_stmt(
                MacroIndicatorTable,
                rows,
                ["name", "timestamp", "source"],
            )
        )
        await self.db.commit()
        return len(rows)

    async def get_latest(self, name: str, limit: int = 1) -> list[dict[str, Any]]:
        result = await self.db.execute(
            select(MacroIndicatorTable)
            .where(MacroIndicatorTable.name == name)
            .order_by(desc(MacroIndicatorTable.timestamp))
            .limit(limit)
        )
        return [
            {
                "name": row.name,
                "timestamp": row.timestamp,
                "value": row.value,
                "unit": row.unit,
                "source": row.source,
                "category": row.category,
            }
            for row in result.scalars().all()
        ]

    async def get_latest_by_name(self, name: str) -> MacroIndicatorTable | None:
        result = await self.db.execute(
            select(MacroIndicatorTable)
            .where(MacroIndicatorTable.name == name)
            .order_by(desc(MacroIndicatorTable.timestamp))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_series(self, name: str, limit: int = 100) -> list[MacroIndicatorTable]:
        result = await self.db.execute(
            select(MacroIndicatorTable)
            .where(MacroIndicatorTable.name == name)
            .order_by(desc(MacroIndicatorTable.timestamp))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_all_latest(self) -> list[MacroIndicatorTable]:
        series_ids = [
            "fed_funds_rate",
            "cpi_yoy",
            "gdp_growth_qoq",
            "unemployment_rate",
            "10y_treasury_yield",
            "2y_treasury_yield",
            "vix",
            "dxy",
        ]
        rows: list[MacroIndicatorTable] = []
        for series_id in series_ids:
            latest = await self.get_latest_by_name(series_id)
            if latest is not None:
                rows.append(latest)
        return rows


class RawPayloadRepository(_BaseRepository):
    async def store(
        self,
        source: str,
        payload_type: str,
        symbol: str,
        data: dict[str, Any],
    ) -> RawPayloadTable:
        payload_hash = _hash_payload(data)
        result = await self.db.execute(
            select(RawPayloadTable).where(RawPayloadTable.payload_hash == payload_hash)
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            return existing

        row = RawPayloadTable(
            source=source,
            provider=source,
            endpoint=f"{payload_type}/{symbol}",
            fetched_at=_now(),
            payload_hash=payload_hash,
            payload_json=data,
            parse_status="success",
        )
        self.db.add(row)
        return await _commit_refresh(self.db, row)

    async def exists_by_hash(self, hash_val: str) -> bool:
        result = await self.db.execute(
            select(RawPayloadTable.id).where(RawPayloadTable.payload_hash == hash_val)
        )
        return result.scalar_one_or_none() is not None

    async def get_by_id(self, payload_id: Any) -> RawPayloadTable | None:
        return await self.db.get(RawPayloadTable, int(payload_id))

    async def update_parse_status(self, payload_id: Any, status: Any, error: str | None = None) -> None:
        row = await self.get_by_id(payload_id)
        if row is None:
            return
        row.parse_status = status.value if hasattr(status, "value") else str(status)
        row.error_message = error
        await self.db.commit()


class SignalRepository(_BaseRepository):
    async def create(self, signal: dict[str, Any]) -> SignalTable:
        asset = await self._resolve_asset(signal.get("asset_id"))
        row = SignalTable(
            asset_id=asset.id if asset else int(signal["asset_id"]),
            symbol=str(signal.get("symbol") or (asset.symbol if asset else "")) or None,
            timestamp=_to_datetime(signal.get("timestamp")) or _now(),
            horizon=str(signal.get("horizon", "swing")),
            signal_type=str(signal.get("signal_type", "composite")),
            direction=str(signal.get("direction", "neutral")),
            score=float(signal.get("score", 0.0)),
            confidence=float(signal.get("confidence", 0.5)),
            expected_return_bucket=signal.get("expected_return_bucket"),
            risk_bucket=signal.get("risk_bucket"),
            main_drivers_json=signal.get("main_drivers_json"),
            evidence_ids=_json_list(signal.get("evidence_ids")),
            reasoning=str(signal.get("reasoning", "")),
            counterarguments=_json_list(signal.get("counterarguments")),
            risk_flags=_json_list(signal.get("risk_flags")),
            created_by=str(signal.get("created_by", "system")),
            version=str(signal.get("version", "1.0")),
        )
        self.db.add(row)
        return await _commit_refresh(self.db, row)

    async def get_by_asset(self, asset_id: Any, limit: int = 20) -> list[SignalTable]:
        asset = await self._resolve_asset(asset_id)
        if asset is None:
            return []
        result = await self.db.execute(
            select(SignalTable)
            .where(SignalTable.asset_id == asset.id)
            .order_by(desc(SignalTable.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_latest_by_asset(self, asset_id: Any) -> SignalTable | None:
        rows = await self.get_by_asset(asset_id, limit=1)
        return rows[0] if rows else None

    async def get_recent(self, limit: int = 50) -> list[SignalTable]:
        result = await self.db.execute(
            select(SignalTable)
            .order_by(desc(SignalTable.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id(self, signal_id: Any) -> SignalTable | None:
        return await self.db.get(SignalTable, int(signal_id))


class DailyBriefingRepository(_BaseRepository):
    async def create(self, briefing: dict[str, Any]) -> DailyBriefingTable:
        raw_date = briefing.get("date")
        if isinstance(raw_date, date):
            date_str = raw_date.isoformat()
        else:
            date_str = str(raw_date)

        existing = await self.get_by_date(date_str)
        if existing is not None:
            return existing

        row = DailyBriefingTable(
            date=date_str,
            market_regime_summary=str(briefing.get("market_regime_summary", "")),
            macro_summary=str(briefing.get("macro_summary", "")),
            equity_summary=str(briefing.get("equity_summary", "")),
            etf_summary=str(briefing.get("etf_summary", "")),
            bond_summary=str(briefing.get("bond_summary", "")),
            crypto_summary=str(briefing.get("crypto_summary", "")),
            top_opportunities=briefing.get("top_opportunities"),
            top_risks=briefing.get("top_risks"),
            unusual_social_activity=briefing.get("unusual_social_activity"),
            major_news_events=briefing.get("major_news_events"),
            watchlist_changes=briefing.get("watchlist_changes"),
            evidence_ids=briefing.get("evidence_ids"),
            disclaimer=str(briefing.get("disclaimer", "")),
        )
        self.db.add(row)
        return await _commit_refresh(self.db, row)

    async def get_latest(self) -> DailyBriefingTable | None:
        result = await self.db.execute(
            select(DailyBriefingTable)
            .order_by(desc(DailyBriefingTable.date))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_date(self, date_str: str) -> DailyBriefingTable | None:
        result = await self.db.execute(
            select(DailyBriefingTable).where(DailyBriefingTable.date == date_str)
        )
        return result.scalar_one_or_none()


class PortfolioProfileRepository(_BaseRepository):
    async def get_default(self) -> PortfolioProfileTable | None:
        result = await self.db.execute(
            select(PortfolioProfileTable).order_by(PortfolioProfileTable.id).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, profile_id: int) -> PortfolioProfileTable | None:
        return await self.db.get(PortfolioProfileTable, profile_id)

    async def upsert(self, profile: PortfolioProfile) -> PortfolioProfileTable:
        existing = None
        if profile.id is not None:
            existing = await self.get_by_id(profile.id)
        if existing is None:
            result = await self.db.execute(
                select(PortfolioProfileTable).where(PortfolioProfileTable.name == profile.name)
            )
            existing = result.scalar_one_or_none()

        values = {
            "name": profile.name,
            "risk_bucket": profile.risk_bucket,
            "time_horizon_years": profile.time_horizon_years,
            "max_drawdown_tolerance": profile.max_drawdown_tolerance,
            "use_crypto": profile.use_crypto,
            "use_precious_metals": profile.use_precious_metals,
            "min_liquidity_months": profile.min_liquidity_months,
            "avoid_leverage": profile.avoid_leverage,
            "single_stock_soft_cap": profile.single_stock_soft_cap,
            "single_stock_hard_cap": profile.single_stock_hard_cap,
            "notes": profile.notes,
        }
        if existing is not None:
            for key, value in values.items():
                setattr(existing, key, value)
            return await _commit_refresh(self.db, existing)

        row = PortfolioProfileTable(**values)
        self.db.add(row)
        return await _commit_refresh(self.db, row)

    async def set_positions(self, profile_id: int, positions: list[PortfolioPosition]) -> None:
        await self.db.execute(
            delete(PortfolioPositionTable).where(PortfolioPositionTable.profile_id == profile_id)
        )
        for position in positions:
            self.db.add(
                PortfolioPositionTable(
                    profile_id=profile_id,
                    symbol=position.symbol,
                    quantity=position.quantity,
                    market_value=position.market_value,
                    cost_basis=position.cost_basis,
                    portfolio_weight=position.portfolio_weight,
                    asset_class=position.asset_class,
                    theme_tags=position.theme_tags,
                    is_speculative=position.is_speculative,
                )
            )
        await self.db.commit()

    async def get_positions(self, profile_id: int) -> list[PortfolioPositionTable]:
        result = await self.db.execute(
            select(PortfolioPositionTable)
            .where(PortfolioPositionTable.profile_id == profile_id)
            .order_by(PortfolioPositionTable.symbol)
        )
        return list(result.scalars().all())


class PortfolioPolicyRepository(_BaseRepository):
    async def replace_rules(self, profile_id: int, rules: list[PolicyRule]) -> None:
        await self.db.execute(
            delete(PortfolioPolicyRuleTable).where(PortfolioPolicyRuleTable.profile_id == profile_id)
        )
        for rule in rules:
            self.db.add(
                PortfolioPolicyRuleTable(
                    profile_id=profile_id,
                    rule_name=rule.rule_name,
                    rule_type=rule.rule_type,
                    target_weight=rule.target_weight,
                    soft_cap=rule.soft_cap,
                    hard_cap=rule.hard_cap,
                    minimum_weight=rule.minimum_weight,
                    asset_class=rule.asset_class,
                    theme_tag=rule.theme_tag,
                    symbol=rule.symbol,
                    is_active=rule.is_active,
                )
            )
        await self.db.commit()

    async def get_rules(self, profile_id: int) -> list[PortfolioPolicyRuleTable]:
        result = await self.db.execute(
            select(PortfolioPolicyRuleTable)
            .where(PortfolioPolicyRuleTable.profile_id == profile_id)
            .order_by(PortfolioPolicyRuleTable.id)
        )
        return list(result.scalars().all())
