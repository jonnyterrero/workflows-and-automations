"""Daily market briefing generator."""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from typing import Any

import structlog

from packages.ai_research.llm_adapter import DISCLAIMER, LLMAdapter
from packages.storage.repositories import (
    AssetRepository, DailyBriefingRepository, MacroRepository,
    NewsRepository, SignalRepository, SocialPostRepository,
)

logger = structlog.get_logger()

_SYSTEM = """You are a senior financial research analyst. Your job is to produce
structured daily market briefings from evidence stored in the database.

Rules:
- Only cite evidence that has been explicitly provided in this prompt (by ID)
- Never invent data, sources, or facts not in the provided context
- Flag uncertainty clearly
- Do not give direct buy/sell recommendations
- Present balanced views with counterarguments
- Every summary must be traceable to evidence

Output: valid JSON matching the DailyBriefing schema."""

_SCHEMA_HINT = """{
  "market_regime_summary": "string",
  "macro_summary": "string",
  "equity_summary": "string",
  "etf_summary": "string",
  "bond_summary": "string",
  "crypto_summary": "string",
  "top_opportunities": [{"symbol": "...", "thesis": "...", "confidence": 0.0, "evidence_ids": []}],
  "top_risks": [{"description": "...", "severity": "low|medium|high", "evidence_ids": []}],
  "unusual_social_activity": [{"symbol": "...", "activity": "...", "evidence_ids": []}],
  "major_news_events": [{"headline": "...", "impact": "...", "evidence_ids": []}],
  "watchlist_changes": []
}"""


class DailyBriefingGenerator:
    def __init__(self, db_session_factory: Any) -> None:
        self.db_factory = db_session_factory
        self.llm = LLMAdapter()

    async def generate(self, briefing_date: date | None = None) -> dict[str, Any]:
        today = briefing_date or date.today()
        logger.info("generating_daily_briefing", date=today.isoformat())

        async with self.db_factory() as db:
            asset_repo = AssetRepository(db)
            news_repo = NewsRepository(db)
            social_repo = SocialPostRepository(db)
            macro_repo = MacroRepository(db)
            signal_repo = SignalRepository(db)
            briefing_repo = DailyBriefingRepository(db)

            # Collect context
            watchlist = await asset_repo.get_watchlist()
            recent_news = await news_repo.get_recent(limit=30, hours_back=24)
            trending_social = await social_repo.get_trending(limit=20, hours_back=12)
            macro_latest = await macro_repo.get_all_latest()
            recent_signals = await signal_repo.get_recent(limit=20)

            # Build evidence index
            evidence_ids: list[int] = []
            evidence_ids.extend([a.id for a in recent_news if a.id])

            # Build context for LLM
            news_context = "\n".join([
                f"[NEWS-{a.id}] {a.source}: {a.title} (credibility={a.credibility_score:.1f})"
                for a in recent_news[:15]
            ])
            social_context = "\n".join([
                f"[SOCIAL-{p.id}] {p.source_community}: {p.text[:150]} (sentiment={p.sentiment_score:.2f})"
                for p in trending_social[:10]
            ])
            macro_context = "\n".join([
                f"  {m.name}: {m.value} {m.unit}" for m in macro_latest
            ])
            signal_context = "\n".join([
                f"  Signal-{s.id}: {s.asset_id} | direction={s.direction} | score={s.score:.1f} | conf={s.confidence:.2f}"
                for s in recent_signals[:10]
            ])
            watchlist_symbols = ", ".join([a.symbol for a in watchlist])

            user_prompt = f"""Date: {today.isoformat()}
Watchlist: {watchlist_symbols}

MACRO INDICATORS:
{macro_context or "No macro data available."}

RECENT NEWS (last 24h):
{news_context or "No recent news."}

TRENDING SOCIAL (last 12h):
{social_context or "No social data."}

RECENT SIGNALS:
{signal_context or "No signals generated yet."}

Generate a comprehensive daily briefing. For each section, cite the specific
evidence IDs from above (e.g., [NEWS-42], [SOCIAL-7]).
Only reference IDs that appear above."""

            briefing_data = await self.llm.complete_json(
                _SYSTEM, user_prompt, schema_hint=_SCHEMA_HINT, max_tokens=3000,
            )

            if not briefing_data:
                briefing_data = self._fallback_briefing(
                    today, recent_news, macro_latest, recent_signals, watchlist,
                )

            briefing_dict = {
                "date": today,
                "market_regime_summary": briefing_data.get("market_regime_summary", "Market regime assessment pending."),
                "macro_summary": briefing_data.get("macro_summary", macro_context[:500] if macro_context else "No macro data."),
                "equity_summary": briefing_data.get("equity_summary", "Equity market data collected."),
                "etf_summary": briefing_data.get("etf_summary", "ETF data collected."),
                "bond_summary": briefing_data.get("bond_summary", "Bond/rate data collected."),
                "crypto_summary": briefing_data.get("crypto_summary", "Crypto market data collected."),
                "top_opportunities": briefing_data.get("top_opportunities", []),
                "top_risks": briefing_data.get("top_risks", []),
                "unusual_social_activity": briefing_data.get("unusual_social_activity", []),
                "major_news_events": briefing_data.get("major_news_events", []),
                "watchlist_changes": briefing_data.get("watchlist_changes", []),
                "evidence_ids": evidence_ids,
                "disclaimer": DISCLAIMER,
            }
            row = await briefing_repo.create(briefing_dict)
            await db.commit()
            logger.info("daily_briefing_created", date=today.isoformat(), id=row.id)
            return briefing_dict

    def _fallback_briefing(
        self, today: date, news: list, macro: list, signals: list, watchlist: list,
    ) -> dict[str, Any]:
        macro_str = "; ".join(f"{m.name}={m.value}{m.unit}" for m in macro[:5])
        return {
            "market_regime_summary": f"[DEMO] Market data collected for {today}. Macro: {macro_str[:200]}",
            "macro_summary": f"Macro context: {macro_str[:300]}. Yield curve data available.",
            "equity_summary": f"Watchlist: {', '.join(a.symbol for a in watchlist)}. {len([s for s in signals if 'bullish' in str(s.direction)])} bullish signals.",
            "etf_summary": "ETF data available for SPY, QQQ, TLT.",
            "bond_summary": "Bond market conditions tracked via TLT and yield curve data.",
            "crypto_summary": "Crypto market data available for BTC-USD, ETH-USD.",
            "top_opportunities": [],
            "top_risks": [],
            "unusual_social_activity": [],
            "major_news_events": [{"headline": a.title, "impact": "unknown", "evidence_ids": [a.id]} for a in news[:3] if a.id],
            "watchlist_changes": [],
        }
