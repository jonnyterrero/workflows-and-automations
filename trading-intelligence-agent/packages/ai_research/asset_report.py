"""Asset-specific research report generator."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

import structlog

from packages.ai_research.llm_adapter import DISCLAIMER, LLMAdapter
from packages.analytics.technicals import TechnicalAnalyzer
from packages.news_intel.collector import NewsCollector
from packages.social_intel.sentiment import SentimentScorer
from packages.storage.repositories import (
    AssetRepository, MacroRepository, MarketPriceRepository,
    FilingRepository,
    ModelFeatureRepository,
    NewsRepository,
    SocialPostRepository,
    SignalRepository,
)

logger = structlog.get_logger()

_SYSTEM = """You are a senior equity and crypto research analyst. Generate a structured
research report for the given asset based ONLY on the provided evidence.

Rules:
- Cite specific evidence IDs [NEWS-X], [SIGNAL-Y] in your analysis
- Present both bull and bear cases with equal rigor
- Flag all risk factors
- Never invent data not in the provided context
- Do not give direct financial advice
Output: valid JSON matching the AssetResearchReport schema."""

_SCHEMA_HINT = """{
  "current_context": "string",
  "bullish_case": "string",
  "bearish_case": "string",
  "technical_context": "string",
  "fundamental_context": "string",
  "macro_context": "string",
  "sentiment_context": "string",
  "risk_flags": ["string"],
  "conclusion": "string",
  "confidence": 0.0,
  "suggested_next_steps": ["string"]
}"""


class AssetResearchReportGenerator:
    def __init__(self, db_session_factory: Any) -> None:
        self.db_factory = db_session_factory
        self.llm = LLMAdapter()
        self.analyzer = TechnicalAnalyzer()
        self.sentiment = SentimentScorer()

    async def generate(self, symbol: str) -> dict[str, Any]:
        logger.info("generating_asset_report", symbol=symbol)
        today = date.today()

        async with self.db_factory() as db:
            asset_repo = AssetRepository(db)
            price_repo = MarketPriceRepository(db)
            news_repo = NewsRepository(db)
            social_repo = SocialPostRepository(db)
            signal_repo = SignalRepository(db)
            macro_repo = MacroRepository(db)
            feature_repo = ModelFeatureRepository(db)
            filing_repo = FilingRepository(db)

            asset = await asset_repo.get_by_symbol(symbol)
            if not asset:
                return {"error": f"Asset {symbol} not found", "symbol": symbol, "disclaimer": DISCLAIMER}

            prices = await price_repo.get_range(
                asset.id,
                start=datetime.now(tz=timezone.utc) - timedelta(days=200),
                end=datetime.now(tz=timezone.utc),
            )
            price_dicts = [
                {"close": p.close, "high": p.high or p.close, "low": p.low or p.close,
                 "open": p.open or p.close, "volume": p.volume or 0}
                for p in prices
            ]
            tech = self.analyzer.compute(price_dicts)

            news = await news_repo.get_by_symbol(symbol, limit=20, hours_back=72)
            social = await social_repo.get_by_symbol(symbol, limit=15, hours_back=48)
            signals = await signal_repo.get_by_asset(asset.id, limit=5)
            macro_all = await macro_repo.get_all_latest()
            latest_features = await feature_repo.get_latest(symbol)
            recent_filings = await filing_repo.get_recent_by_symbol(symbol, limit=5, days_back=120)

            evidence_ids: list[int] = []
            evidence_ids.extend([a.id for a in news if a.id])

            news_ctx = "\n".join([
                f"[NEWS-{a.id}] {a.source}: {a.title} (cred={a.credibility_score:.1f}, pub={a.published_at})"
                for a in news[:10]
            ])
            social_ctx = "\n".join([
                f"[SOCIAL-{p.id}] {p.source_community}: {p.text[:120]} (sent={p.sentiment_score:.2f}, spam={p.toxicity_or_spam_score:.2f})"
                for p in social[:8]
            ])
            signal_ctx = "\n".join([
                f"[SIGNAL-{s.id}] dir={s.direction}, score={s.score:.1f}, conf={s.confidence:.2f}: {s.reasoning[:100]}"
                for s in signals
            ])
            macro_ctx = " | ".join([f"{m.name}={m.value}{m.unit}" for m in macro_all[:6]])
            feature_payload = latest_features.features_json if latest_features else {}
            fundamental_notes = feature_payload.get("fundamental_notes") or []
            catalyst_notes = feature_payload.get("catalyst_notes") or []
            next_earnings = feature_payload.get("next_earnings_date")
            filing_ctx = "\n".join([
                f"{row.filing_type} filed {row.filed_at.date().isoformat()}: {row.url}"
                for row in recent_filings[:4]
            ])
            fundamental_ctx = " | ".join(filter(None, [
                f"fundamental_score={feature_payload.get('fundamental_score')}" if feature_payload else "",
                f"event_catalyst_score={feature_payload.get('event_catalyst_score')}" if feature_payload else "",
                f"next_earnings={next_earnings}" if next_earnings else "",
                "; ".join(fundamental_notes[:2]) if fundamental_notes else "",
                "; ".join(catalyst_notes[:2]) if catalyst_notes else "",
            ]))
            tech_ctx = (
                f"Close={tech.get('latest_close')}, RSI={tech.get('rsi_14')}, "
                f"Trend={tech.get('trend_direction')}, Vol20d={tech.get('vol_20d')}, "
                f"MACD={tech.get('macd')}, BB_width={tech.get('bb_width')}"
            )

            user_prompt = f"""Asset: {symbol} ({asset.name})
Asset Class: {asset.asset_class}
Date: {today.isoformat()}

TECHNICAL INDICATORS:
{tech_ctx}

MACRO CONTEXT:
{macro_ctx or "Not available"}

NEWS (last 72h):
{news_ctx or "No recent news"}

SOCIAL SENTIMENT (last 48h):
{social_ctx or "No social data"}

FUNDAMENTALS & CATALYSTS:
{fundamental_ctx or "No fundamentals/catalyst data"}

RECENT FILINGS:
{filing_ctx or "No recent filings"}

RECENT SIGNALS:
{signal_ctx or "No signals generated"}

Generate a comprehensive research report. Cite evidence IDs explicitly.
Only reference evidence IDs listed above."""

            report_data = await self.llm.complete_json(
                _SYSTEM, user_prompt, schema_hint=_SCHEMA_HINT, max_tokens=2500,
            )

            if not report_data:
                report_data = self._fallback_report(symbol, tech, news, signals)

            return {
                "asset_id": asset.id,
                "date": today,
                "current_context": report_data.get("current_context", f"Analysis for {symbol} as of {today}"),
                "bullish_case": report_data.get("bullish_case", "Bullish analysis requires more data."),
                "bearish_case": report_data.get("bearish_case", "Bearish analysis requires more data."),
                "technical_context": report_data.get("technical_context", tech_ctx),
                "fundamental_context": report_data.get(
                    "fundamental_context",
                    fundamental_ctx or "No fundamentals snapshot available.",
                ),
                "macro_context": report_data.get("macro_context", macro_ctx),
                "sentiment_context": report_data.get("sentiment_context", f"{len(news)} news articles, {len(social)} social posts analyzed."),
                "risk_flags": report_data.get("risk_flags", []),
                "conclusion": report_data.get("conclusion", "Insufficient data for definitive conclusion."),
                "confidence": float(report_data.get("confidence", 0.5)),
                "evidence_ids": evidence_ids,
                "suggested_next_steps": report_data.get("suggested_next_steps", ["Monitor news flow", "Watch for volume confirmation"]),
                "disclaimer": DISCLAIMER,
            }

    def _fallback_report(
        self, symbol: str, tech: dict, news: list, signals: list,
    ) -> dict[str, Any]:
        trend = tech.get("trend_direction", "sideways")
        rsi = tech.get("rsi_14")
        return {
            "current_context": f"[DEMO] {symbol} technical trend: {trend}. RSI: {rsi}.",
            "bullish_case": f"Upside drivers require LLM analysis. Set API key to enable.",
            "bearish_case": f"Downside risks require LLM analysis. Set API key to enable.",
            "technical_context": f"Trend={trend}, RSI={rsi}, Momentum={tech.get('momentum_score'):.2f}",
            "fundamental_context": "Not available in demo mode.",
            "macro_context": "See /signals and /news endpoints for context.",
            "sentiment_context": f"{len(news)} news articles indexed.",
            "risk_flags": ["Demo mode — LLM analysis not available"],
            "conclusion": "Enable LLM provider (OPENAI_API_KEY or ANTHROPIC_API_KEY) for full analysis.",
            "confidence": 0.3,
            "suggested_next_steps": ["Set LLM API key in .env", "Run make run-api"],
        }
