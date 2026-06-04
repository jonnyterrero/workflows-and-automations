"""Tests for ticker extraction logic."""
import pytest
from packages.social_intel.ticker_extractor import TickerExtractor

e = TickerExtractor()


def test_dollar_prefix():
    assert "AAPL" in e.extract("$AAPL earnings beat estimates today")


def test_known_ticker_bare_caps():
    assert "NVDA" in e.extract("NVDA up 5% on AI news")


def test_ambiguous_word_excluded():
    # "AI" is in AMBIGUOUS_WORDS
    result = e.extract("The AI revolution is here")
    assert "AI" not in result


def test_apple_fruit_excluded():
    result = e.extract("I like apple the fruit")
    assert "AAPL" not in result


def test_spy_in_options_context():
    result = e.extract("SPY calls expiring Friday")
    assert "SPY" in result


def test_btc_normalization():
    result = e.extract("I'm buying $BTC and $ETH today")
    assert "BTC-USD" in result
    assert "ETH-USD" in result


def test_multi_ticker():
    result = e.extract("$AAPL $NVDA $TSLA all up big today")
    assert set(["AAPL", "NVDA", "TSLA"]).issubset(set(result))


def test_empty_text():
    assert e.extract("") == []


def test_normalize_dollar():
    assert e.normalize_symbol("$AAPL") == "AAPL"


def test_normalize_crypto():
    assert e.normalize_symbol("BTC") == "BTC-USD"


def test_extract_with_context_confidence():
    results = e.extract_with_context("$AAPL beats earnings")
    aapl = next((r for r in results if r["ticker"] == "AAPL"), None)
    assert aapl is not None
    assert aapl["confidence"] == 1.0


def test_no_tickers_in_generic_text():
    result = e.extract("The market is uncertain today")
    assert result == []
