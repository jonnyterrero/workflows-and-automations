"""Transparent, decomposable signal scoring engine."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import yaml
import structlog

from packages.core_models.pydantic_models import SignalDirection, SignalHorizon, SignalType

logger = structlog.get_logger()

_WEIGHTS_FILE = os.path.join(
    os.path.dirname(__file__), "..", "..", "config", "signal_weights.yaml"
)


def _load_weights() -> dict[str, Any]:
    try:
        with open(_WEIGHTS_FILE) as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {
            "weights": {
                "market_trend": 0.20, "momentum": 0.10, "volume": 0.08,
                "volatility": 0.05, "news_sentiment": 0.18, "social_sentiment": 0.10,
                "macro_alignment": 0.12, "fundamental": 0.10, "event_catalyst": 0.07,
            },
            "penalties": {
                "risk_penalty": 0.15, "contradiction": 0.10, "low_confidence": 0.05,
            },
            "thresholds": {"min_evidence_count": 2, "spam_score_max": 0.60},
        }


_CONFIG = _load_weights()
_W = _CONFIG["weights"]
_P = _CONFIG["penalties"]
_T = _CONFIG["thresholds"]


@dataclass
class SignalComponents:
    market_trend_score: float = 0.0
    momentum_score: float = 0.0
    volume_score: float = 0.0
    volatility_score: float = 0.0
    news_sentiment_score: float = 0.0
    social_sentiment_score: float = 0.0
    macro_alignment_score: float = 0.0
    fundamental_score: float = 0.0
    event_catalyst_score: float = 0.0
    risk_penalty: float = 0.0
    contradiction_penalty: float = 0.0
    low_confidence_penalty: float = 0.0
    risk_flags: list[str] = field(default_factory=list)
    evidence_ids: list[int] = field(default_factory=list)
    counterarguments: list[str] = field(default_factory=list)
    reasoning_parts: list[str] = field(default_factory=list)


class SignalScorer:
    """Compute a transparent composite signal score from component sub-scores."""

    def score_from_technicals(self, technicals: dict[str, Any]) -> float:
        """Convert technical analysis output to -1.0 to +1.0 market trend score."""
        if not technicals:
            return 0.0
        trend = technicals.get("trend_direction", "sideways")
        momentum = float(technicals.get("momentum_score") or 0.0)
        rsi = technicals.get("rsi_14")
        trend_score = {"uptrend": 0.6, "downtrend": -0.6, "sideways": 0.0}.get(trend, 0.0)
        combined = (trend_score * 0.6 + momentum * 0.4)
        return max(-1.0, min(1.0, combined))

    def score_from_news_sentiment(self, sentiment_data: dict[str, Any]) -> float:
        """Convert news sentiment summary to -1.0 to +1.0 score."""
        if not sentiment_data:
            return 0.0
        cred_sent = float(sentiment_data.get("credibility_weighted_sentiment") or
                          sentiment_data.get("avg_sentiment") or 0.0)
        return max(-1.0, min(1.0, cred_sent))

    def score_from_social_sentiment(
        self, posts_sentiment: float, spam_ratio: float = 0.0,
    ) -> float:
        """Adjust social sentiment by spam/credibility."""
        adjusted = posts_sentiment * (1.0 - min(spam_ratio, 0.8))
        return max(-1.0, min(1.0, adjusted))

    def score_macro_alignment(
        self, asset_class: str, macro_context: str,
    ) -> float:
        """Score how well current macro environment aligns with the asset class."""
        mc = macro_context.lower()
        inverted = "inverted" in mc
        if asset_class in ("bond", "bond_etf"):
            if inverted:
                return 0.3
            return -0.1
        if asset_class in ("stock", "etf", "index"):
            if inverted:
                return -0.3
            vix_high = "vix: 2" in mc or "vix: 3" in mc  # rough check
            return -0.2 if vix_high else 0.1
        if asset_class == "crypto":
            if "inflation" in mc and float(
                mc.split("cpi:")[1].split("%")[0].strip() if "cpi:" in mc else "3"
            ) > 4:
                return 0.2
            return 0.0
        return 0.0

    def score_volatility_penalty(self, annualized_vol: float | None) -> float:
        """Returns a negative adjustment for high volatility assets."""
        if annualized_vol is None:
            return 0.0
        threshold = float(_T.get("high_volatility_vol", 0.4))
        if annualized_vol > threshold:
            excess = min(annualized_vol - threshold, 1.0)
            return -excess * 0.5
        return 0.0

    def compute_composite(
        self, components: SignalComponents, evidence_count: int,
    ) -> tuple[float, float, SignalDirection]:
        """
        Returns (score: -100..+100, confidence: 0..1, direction).

        Formula:
          raw = Σ(weight_i * component_i)   # range -1 to +1
          penalties applied
          score = raw * 100
          confidence based on evidence count and contradiction
        """
        w = _W
        raw = (
            w["market_trend"]    * components.market_trend_score
            + w["momentum"]      * components.momentum_score
            + w["volume"]        * components.volume_score
            + w["volatility"]    * components.volatility_score
            + w["news_sentiment"] * components.news_sentiment_score
            + w["social_sentiment"] * components.social_sentiment_score
            + w["macro_alignment"] * components.macro_alignment_score
            + w["fundamental"]   * components.fundamental_score
            + w["event_catalyst"] * components.event_catalyst_score
        )

        p = _P
        pen = (
            components.risk_penalty * p["risk_penalty"]
            + components.contradiction_penalty * p["contradiction"]
            + components.low_confidence_penalty * p["low_confidence"]
        )

        adjusted = max(-1.0, min(1.0, raw - pen))
        score = round(adjusted * 100, 2)

        min_evidence = int(_T.get("min_evidence_count", 2))
        evidence_ratio = min(evidence_count / max(min_evidence, 1), 1.0)
        contradiction_hit = components.contradiction_penalty > 0.3
        confidence = evidence_ratio * (0.7 if contradiction_hit else 1.0)
        if len(components.risk_flags) > 3:
            confidence *= 0.8
        confidence = round(max(0.0, min(1.0, confidence)), 3)

        if score > 15:
            direction = SignalDirection.BULLISH
        elif score < -15:
            direction = SignalDirection.BEARISH
        elif abs(score) > 5 and components.contradiction_penalty > 0.2:
            direction = SignalDirection.MIXED
        else:
            direction = SignalDirection.NEUTRAL

        return score, confidence, direction

    def build_signal_dict(
        self,
        asset_id: int,
        components: SignalComponents,
        evidence_count: int,
        horizon: SignalHorizon = SignalHorizon.SWING,
        signal_type: SignalType = SignalType.COMPOSITE,
    ) -> dict[str, Any]:
        score, confidence, direction = self.compute_composite(components, evidence_count)
        reasoning = "; ".join(components.reasoning_parts) if components.reasoning_parts else "Signal computed from available data."
        return {
            "asset_id": asset_id,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "horizon": horizon.value,
            "signal_type": signal_type.value,
            "direction": direction.value,
            "score": score,
            "confidence": confidence,
            "evidence_ids": components.evidence_ids,
            "reasoning": reasoning,
            "counterarguments": components.counterarguments,
            "risk_flags": components.risk_flags,
            "created_by": "signal_engine",
            "version": "1.0",
        }

    async def run_for_asset(
        self,
        asset_id: int,
        symbol: str,
        asset_class: str,
        db: Any,
        horizon: SignalHorizon = SignalHorizon.SWING,
    ) -> dict[str, Any]:
        """Full signal computation pipeline for a single asset."""
        from packages.storage.repositories import MarketPriceRepository, NewsRepository, SocialPostRepository
        from packages.analytics.technicals import TechnicalAnalyzer
        from packages.news_intel.collector import NewsCollector
        from packages.social_intel.sentiment import SentimentScorer
        from packages.risk_engine.risk_flags import RiskEngine
        from packages.macro_data.collector import MacroDataCollector

        components = SignalComponents()
        analyzer = TechnicalAnalyzer()
        sentiment = SentimentScorer()
        risk_engine = RiskEngine()

        # Technical score
        price_repo = MarketPriceRepository(db)
        prices = await price_repo.get_range(
            asset_id,
            start=datetime(2020, 1, 1, tzinfo=timezone.utc),
            end=datetime.now(tz=timezone.utc),
        )
        price_dicts = [
            {"close": p.close, "high": p.high or p.close, "low": p.low or p.close,
             "open": p.open or p.close, "volume": p.volume or 0}
            for p in prices[-200:]
        ]
        tech = analyzer.compute(price_dicts)
        components.market_trend_score = self.score_from_technicals(tech)
        components.momentum_score = float(tech.get("momentum_score") or 0.0)
        vol = tech.get("vol_20d")
        components.volatility_score = self.score_volatility_penalty(vol)
        if tech.get("technical_signal") == "bullish":
            components.reasoning_parts.append(f"Technical: {tech.get('trend_direction')} trend, RSI={tech.get('rsi_14', 'N/A')}")
        elif tech.get("technical_signal") == "bearish":
            components.reasoning_parts.append(f"Technical: {tech.get('trend_direction')} trend (bearish)")
            components.counterarguments.append("Technical indicators show bearish momentum.")

        # News sentiment
        news_repo = NewsRepository(db)
        articles = await news_repo.get_by_symbol(symbol, limit=20, hours_back=72)
        if articles:
            scores = [sentiment.score_text((a.title or "") + " " + (a.raw_text or "")) for a in articles]
            avg_news = sum(scores) / len(scores)
            components.news_sentiment_score = avg_news
            components.evidence_ids.extend([a.id for a in articles if a.id])
            components.reasoning_parts.append(f"News: {len(articles)} articles, avg sentiment={avg_news:.2f}")

        # Social sentiment
        social_repo = SocialPostRepository(db)
        posts = await social_repo.get_by_symbol(symbol, limit=20, hours_back=48)
        if posts:
            valid_posts = [p for p in posts if p.toxicity_or_spam_score < 0.6]
            if valid_posts:
                avg_social = sum(p.sentiment_score for p in valid_posts) / len(valid_posts)
                spam_excluded = len(posts) - len(valid_posts)
                components.social_sentiment_score = self.score_from_social_sentiment(avg_social)
                components.reasoning_parts.append(
                    f"Social: {len(valid_posts)} posts (excluded {spam_excluded} high-spam), avg sentiment={avg_social:.2f}"
                )
                if spam_excluded > len(posts) * 0.5:
                    components.contradiction_penalty += 0.2
                    components.risk_flags.append("High social spam ratio — social signals unreliable")

        # Contradiction detection
        if components.news_sentiment_score > 0.3 and components.social_sentiment_score < -0.3:
            components.contradiction_penalty += 0.3
            components.counterarguments.append("News bullish but social sentiment bearish — conflict.")
        elif components.news_sentiment_score < -0.3 and components.social_sentiment_score > 0.3:
            components.contradiction_penalty += 0.3
            components.counterarguments.append("News bearish but social sentiment bullish — conflict.")

        # Risk flags
        flags = await risk_engine.evaluate(symbol, asset_class, tech, vol, articles, posts, db)
        components.risk_flags.extend(flags)
        components.risk_penalty = min(len(flags) * 0.15, 0.6)

        # Low evidence penalty
        if len(components.evidence_ids) < int(_T.get("min_evidence_count", 2)):
            components.low_confidence_penalty = 0.3
            components.risk_flags.append("Insufficient evidence — treat signal with caution")

        return self.build_signal_dict(
            asset_id, components, len(components.evidence_ids), horizon,
        )
