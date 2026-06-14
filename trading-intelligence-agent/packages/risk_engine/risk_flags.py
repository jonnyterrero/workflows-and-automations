"""Risk flag detection engine."""
from __future__ import annotations

from typing import Any


class RiskEngine:
    """Evaluate risk flags for a given asset based on available data."""

    async def evaluate(
        self,
        symbol: str,
        asset_class: str,
        technicals: dict[str, Any],
        annualized_vol: float | None,
        news_articles: list[Any],
        social_posts: list[Any],
        db: Any,
    ) -> list[str]:
        flags: list[str] = []
        asset_kind = asset_class.lower()

        # Volatility
        if annualized_vol and annualized_vol > 0.40:
            flags.append(f"High volatility: {annualized_vol:.1%} annualized (>40% threshold)")
        elif annualized_vol and annualized_vol > 0.60:
            flags.append(f"Extreme volatility: {annualized_vol:.1%} annualized")

        # Social hype
        if social_posts:
            spam_posts = [p for p in social_posts if p.toxicity_or_spam_score > 0.5]
            if len(spam_posts) / max(len(social_posts), 1) > 0.4:
                flags.append("Social hype spike: >40% of posts flagged as spam/hype")
            high_sentiment = [p for p in social_posts if p.sentiment_score > 0.8]
            if len(high_sentiment) / max(len(social_posts), 1) > 0.6:
                flags.append("Extreme positive social sentiment — potential pump risk")

        # Negative news conflict
        if news_articles:
            neg_articles = [
                a for a in news_articles
                if a.credibility_score > 0.7 and hasattr(a, "raw_text") and a.raw_text
                and any(w in (a.raw_text or "").lower() for w in ["fraud", "sec investigation", "default", "bankrupt", "delisted"])
            ]
            if neg_articles:
                flags.append("High-credibility negative news: regulatory/fraud/default risk detected")

        # Macro headwinds (bond/rate sensitive)
        if asset_kind in ("bond", "bond_etf", "cash_equivalent"):
            flags.append("Rate sensitivity: Bond ETFs carry duration risk in rising-rate environments")

        # Crypto-specific
        if asset_kind == "crypto":
            if annualized_vol and annualized_vol > 0.80:
                flags.append("Crypto extreme volatility: >80% annualized vol")
            if social_posts:
                hype_ratio = sum(1 for p in social_posts if p.sentiment_score > 0.7) / max(len(social_posts), 1)
                if hype_ratio > 0.7:
                    flags.append("Crypto hype risk: >70% of posts extremely bullish — FOMO alert")

        # Technical overbought/oversold
        rsi = technicals.get("rsi_14")
        if rsi:
            if rsi > 75:
                flags.append(f"Technically overbought: RSI={rsi:.1f} (>75)")
            elif rsi < 25:
                flags.append(f"Technically oversold: RSI={rsi:.1f} (<25)")

        # Low data quality
        if not news_articles and not social_posts:
            flags.append("Low data quality: No recent news or social data available")

        return flags

    def evaluate_sync(
        self,
        symbol: str,
        asset_class: str,
        technicals: dict[str, Any],
        annualized_vol: float | None,
        news_count: int = 0,
        social_count: int = 0,
        spam_ratio: float = 0.0,
        avg_social_sentiment: float = 0.0,
    ) -> list[str]:
        """Synchronous version for use in signal scoring without DB access."""
        flags: list[str] = []
        asset_kind = asset_class.lower()
        if annualized_vol and annualized_vol > 0.40:
            flags.append(f"High volatility: {annualized_vol:.1%} annualized")
        if spam_ratio > 0.4:
            flags.append("Social hype spike: high spam/hype post ratio")
        if avg_social_sentiment > 0.8:
            flags.append("Extreme positive social sentiment — pump risk")
        if asset_kind in ("bond", "bond_etf", "cash_equivalent"):
            flags.append("Duration/rate sensitivity risk for bond assets")
        if asset_kind == "crypto":
            if annualized_vol and annualized_vol > 0.80:
                flags.append("Crypto extreme volatility (>80% annualized)")
        rsi = technicals.get("rsi_14")
        if rsi and rsi > 75:
            flags.append(f"Overbought: RSI={rsi:.1f}")
        elif rsi and rsi < 25:
            flags.append(f"Oversold: RSI={rsi:.1f}")
        if news_count == 0 and social_count == 0:
            flags.append("No evidence available — signal unreliable")
        return flags
