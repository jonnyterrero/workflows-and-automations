"""Tests for signal scoring math."""
import pytest
from packages.signal_engine.scorer import SignalScorer, SignalComponents
from packages.core_models.pydantic_models import SignalDirection, SignalHorizon


def make_components(**kwargs) -> SignalComponents:
    c = SignalComponents()
    for k, v in kwargs.items():
        setattr(c, k, v)
    return c


def test_bullish_signal():
    scorer = SignalScorer()
    components = make_components(
        market_trend_score=0.8, momentum_score=0.7, news_sentiment_score=0.6,
        social_sentiment_score=0.5,
    )
    score, confidence, direction = scorer.compute_composite(components, evidence_count=5)
    assert direction == SignalDirection.BULLISH
    assert score > 0


def test_bearish_signal():
    scorer = SignalScorer()
    components = make_components(
        market_trend_score=-0.8, momentum_score=-0.7, news_sentiment_score=-0.6,
    )
    score, confidence, direction = scorer.compute_composite(components, evidence_count=5)
    assert direction == SignalDirection.BEARISH
    assert score < 0


def test_neutral_signal():
    scorer = SignalScorer()
    components = SignalComponents()
    score, confidence, direction = scorer.compute_composite(components, evidence_count=3)
    assert direction == SignalDirection.NEUTRAL
    assert abs(score) < 20


def test_risk_penalty_reduces_confidence():
    scorer = SignalScorer()
    clean = make_components(market_trend_score=0.5, news_sentiment_score=0.5)
    risky = make_components(
        market_trend_score=0.5, news_sentiment_score=0.5,
        risk_flags=["flag1", "flag2", "flag3", "flag4", "flag5"],
        risk_penalty=0.5,
    )
    _, conf_clean, _ = scorer.compute_composite(clean, evidence_count=5)
    _, conf_risky, _ = scorer.compute_composite(risky, evidence_count=5)
    assert conf_risky <= conf_clean


def test_score_bounds():
    scorer = SignalScorer()
    components = make_components(
        market_trend_score=10.0, momentum_score=10.0, news_sentiment_score=10.0,
    )
    score, _, _ = scorer.compute_composite(components, evidence_count=10)
    assert -100 <= score <= 100


def test_low_evidence_penalty():
    scorer = SignalScorer()
    low = SignalComponents()
    _, conf_low, _ = scorer.compute_composite(low, evidence_count=0)
    _, conf_high, _ = scorer.compute_composite(low, evidence_count=10)
    assert conf_low <= conf_high


def test_volatility_penalty():
    scorer = SignalScorer()
    score = scorer.score_volatility_penalty(0.6)
    assert score < 0


def test_technicals_score():
    scorer = SignalScorer()
    tech = {
        "trend_direction": "uptrend", "momentum_score": 0.6,
        "technical_signal": "bullish", "rsi_14": 55,
    }
    score = scorer.score_from_technicals(tech)
    assert score > 0


def test_news_sentiment_score():
    scorer = SignalScorer()
    data = {"credibility_weighted_sentiment": 0.7}
    assert scorer.score_from_news_sentiment(data) > 0

    data2 = {"credibility_weighted_sentiment": -0.5}
    assert scorer.score_from_news_sentiment(data2) < 0
