"""Tests for deduplication and hashing utilities."""
import pytest
from packages.normalization.normalizer import compute_content_hash, compute_payload_hash, Deduplicator


def test_content_hash_consistent():
    h1 = compute_content_hash("NVIDIA beats earnings", "https://example.com/1")
    h2 = compute_content_hash("NVIDIA beats earnings", "https://example.com/1")
    assert h1 == h2


def test_content_hash_different():
    h1 = compute_content_hash("Apple announces new iPhone", "https://a.com")
    h2 = compute_content_hash("Tesla cuts prices", "https://b.com")
    assert h1 != h2


def test_payload_hash_dict():
    d = {"symbol": "AAPL", "close": 190.5}
    h1 = compute_payload_hash(d)
    h2 = compute_payload_hash(d)
    assert h1 == h2


def test_payload_hash_key_order_invariant():
    d1 = {"a": 1, "b": 2}
    d2 = {"b": 2, "a": 1}
    assert compute_payload_hash(d1) == compute_payload_hash(d2)


def test_deduplicator_in_memory():
    dedup = Deduplicator()
    h = "abc123"
    assert not dedup.is_duplicate(h)
    dedup.mark_seen(h)
    assert dedup.is_duplicate(h)


def test_deduplicator_different_hashes():
    dedup = Deduplicator()
    dedup.mark_seen("hash1")
    assert not dedup.is_duplicate("hash2")


def test_sentiment_scoring():
    from packages.social_intel.sentiment import SentimentScorer
    scorer = SentimentScorer()
    assert scorer.score_text("NVDA is going to the moon! Bullish rally!") > 0
    assert scorer.score_text("TSLA crash incoming, dump everything") < 0
    assert abs(scorer.score_text("The market is uncertain")) < 0.5


def test_spam_scoring():
    from packages.social_intel.sentiment import SentimentScorer
    scorer = SentimentScorer()
    spam_text = "GUARANTEED RETURNS! 100x!! dm me for discord link BUY NOW"
    legit_text = "Long-term analysis of NVDA's AI chip market position."
    assert scorer.score_spam(spam_text) > scorer.score_spam(legit_text)
