"""Lexicon-based sentiment scoring — no external NLP libraries required."""
from __future__ import annotations

import re

from packages.core_models.pydantic_models import SignalDirection

_BULLISH: list[str] = [
    "moon", "rocket", "calls", "bull", "long", "buy", "buying", "undervalued",
    "upside", "breakout", "surge", "rally", "beat", "upgrade", "outperform",
    "strong", "growth", "positive", "bullish", "squeeze", "ath", "accumulate",
    "diamond hands", "hodl", "pump", "momentum", "earnings beat", "revenue growth",
    "raised guidance", "expansion", "recovery", "bottomed", "support held",
    "golden cross", "oversold", "cheap", "discount", "great value", "winner",
    "printing", "gains", "green", "ripping", "flying", "skyrocket", "explosive",
    "record", "best ever", "all time high", "buy the dip", "buying opportunity",
]

_BEARISH: list[str] = [
    "dump", "crash", "puts", "bear", "short", "sell", "selling", "overvalued",
    "downside", "breakdown", "plunge", "decline", "miss", "downgrade",
    "underperform", "weak", "loss", "negative", "bearish", "rekt", "trapped",
    "distribution", "rejection", "resistance", "failed", "disappointing",
    "missed estimates", "cut guidance", "layoffs", "implosion", "bank run",
    "default", "bankrupt", "delisted", "fraud", "death cross", "overbought",
    "bubble", "expensive", "overpriced", "loser", "dead cat", "red", "bleeding",
    "tanking", "imploding", "collapse", "cut", "miss", "warning", "risk off",
]

_SPAM: list[str] = [
    "pump it", "guaranteed returns", "100x", "easy money", "get rich",
    "secret signal", "follow me", "discord", "telegram", "dm me",
    "insider tip", "buying $", "trust me bro", "to the moon guaranteed",
    "apes together", "not financial advice but buy", "limited time",
    "cant lose", "cant fail", "free signals",
]

_NEGATIONS = frozenset({"not", "no", "never", "without", "barely", "hardly", "isn't", "wasn't", "don't", "won't"})


class SentimentScorer:
    def score_text(self, text: str) -> float:
        lower = text.lower()
        words = re.findall(r"\b[\w']+\b", lower)
        bullish = 0
        bearish = 0
        negate = False
        for i, word in enumerate(words):
            if word in _NEGATIONS:
                negate = True
                continue
            for phrase in _BULLISH:
                if phrase in lower[max(0, lower.find(word) - 5):lower.find(word) + len(word) + 5]:
                    val = -1 if negate else 1
                    if val > 0:
                        bullish += 1
                    else:
                        bearish += 1
                    break
            for phrase in _BEARISH:
                if phrase in lower[max(0, lower.find(word) - 5):lower.find(word) + len(word) + 5]:
                    val = 1 if negate else -1
                    if val > 0:
                        bullish += 1
                    else:
                        bearish += 1
                    break
            if i % 5 == 0:
                negate = False

        # Simpler fallback: direct phrase matching
        bullish_count = sum(1 for p in _BULLISH if p in lower)
        bearish_count = sum(1 for p in _BEARISH if p in lower)
        total = bullish_count + bearish_count
        if total == 0:
            return 0.0
        score = (bullish_count - bearish_count) / total
        return max(-1.0, min(1.0, score))

    def score_spam(self, text: str) -> float:
        lower = text.lower()
        spam_matches = sum(1 for s in _SPAM if s in lower)
        caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        exclamation_ratio = text.count("!") / max(len(text.split()), 1)
        url_count = len(re.findall(r"https?://\S+", text))
        score = (
            spam_matches * 0.3
            + caps_ratio * 0.3
            + min(exclamation_ratio * 2, 0.2)
            + min(url_count * 0.1, 0.2)
        )
        return max(0.0, min(1.0, score))

    def classify_sentiment(self, score: float) -> SignalDirection:
        if score > 0.3:
            return SignalDirection.BULLISH
        if score < -0.3:
            return SignalDirection.BEARISH
        return SignalDirection.NEUTRAL

    def score_credibility(
        self,
        platform: str,
        community: str,
        engagement: float,
        account_age_days: int | None = None,
    ) -> float:
        base_scores = {
            "r/investing": 0.60,
            "r/stocks": 0.55,
            "r/SecurityAnalysis": 0.70,
            "r/CryptoCurrency": 0.40,
            "r/wallstreetbets": 0.30,
            "twitter_verified": 0.50,
            "twitter_unverified": 0.20,
        }
        community_lower = community.lower() if community else ""
        base = 0.4
        for key, score in base_scores.items():
            if key.lower() in community_lower:
                base = score
                break
        if engagement > 0.7:
            base = min(base + 0.1, 0.95)
        if account_age_days and account_age_days > 365:
            base = min(base + 0.1, 0.95)
        return round(base, 3)


class NewsCredibilityScorer:
    TRUSTED: dict[str, float] = {
        "reuters": 0.95, "bloomberg": 0.92, "wsj": 0.90, "ft": 0.90,
        "ap": 0.88, "cnbc": 0.75, "marketwatch": 0.70, "yahoo finance": 0.65,
        "seeking alpha": 0.50, "benzinga": 0.55, "motley fool": 0.45,
        "barrons": 0.85, "the economist": 0.88, "financial times": 0.90,
        "coindesk": 0.65, "cointelegraph": 0.55,
    }

    def score_source(self, source: str) -> float:
        s = source.lower()
        for name, score in self.TRUSTED.items():
            if name in s:
                return score
        return 0.4

    def score_article(self, title: str, source: str, published_at_hours_ago: float) -> float:
        base = self.score_source(source)
        if published_at_hours_ago > 72:
            recency_penalty = min((published_at_hours_ago - 72) / 168, 0.2)
            base = max(0.1, base - recency_penalty)
        return round(base, 3)
