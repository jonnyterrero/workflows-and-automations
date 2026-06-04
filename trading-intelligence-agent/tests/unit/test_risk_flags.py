"""Tests for risk flag logic."""
import pytest
from packages.risk_engine.risk_flags import RiskEngine


def test_high_volatility_flag():
    engine = RiskEngine()
    flags = engine.evaluate_sync("SPY", "etf", {}, annualized_vol=0.55)
    assert any("volatility" in f.lower() for f in flags)


def test_no_flags_normal_conditions():
    engine = RiskEngine()
    tech = {"rsi_14": 50, "trend_direction": "uptrend"}
    flags = engine.evaluate_sync("AAPL", "stock", tech, annualized_vol=0.20, news_count=5, social_count=3)
    assert not any("volatility" in f.lower() for f in flags)


def test_bond_duration_flag():
    engine = RiskEngine()
    flags = engine.evaluate_sync("TLT", "bond_etf", {}, annualized_vol=0.10)
    assert any("duration" in f.lower() or "rate" in f.lower() for f in flags)


def test_crypto_high_vol_flag():
    engine = RiskEngine()
    flags = engine.evaluate_sync("BTC-USD", "crypto", {}, annualized_vol=0.90)
    assert any("crypto" in f.lower() or "volatility" in f.lower() for f in flags)


def test_overbought_rsi():
    engine = RiskEngine()
    flags = engine.evaluate_sync("NVDA", "stock", {"rsi_14": 80}, annualized_vol=0.30)
    assert any("overbought" in f.lower() for f in flags)


def test_oversold_rsi():
    engine = RiskEngine()
    flags = engine.evaluate_sync("TSLA", "stock", {"rsi_14": 20}, annualized_vol=0.30)
    assert any("oversold" in f.lower() for f in flags)


def test_no_evidence_flag():
    engine = RiskEngine()
    flags = engine.evaluate_sync("UNKNOWN", "stock", {}, annualized_vol=None, news_count=0, social_count=0)
    assert any("evidence" in f.lower() for f in flags)


def test_social_hype_flag():
    engine = RiskEngine()
    flags = engine.evaluate_sync(
        "MEME", "stock", {}, annualized_vol=0.50,
        social_count=10, spam_ratio=0.6, avg_social_sentiment=0.9,
    )
    assert any("spam" in f.lower() or "hype" in f.lower() for f in flags)
