"""Tests for crypto RSS catalog loader."""
from __future__ import annotations

from pathlib import Path

from packages.data_providers.live.crypto_feeds_catalog import (
    catalog_summary,
    load_crypto_rss_catalog,
)


def test_catalog_loads_feeds() -> None:
    feeds = load_crypto_rss_catalog()
    assert len(feeds) >= 10
    names = {f.name for f in feeds}
    assert "CoinDesk" in names
    assert "Bloomberg Crypto" in names
    assert "SEC Press Releases" in names


def test_catalog_summary_structure() -> None:
    summary = catalog_summary()
    assert summary["rss_feed_count"] >= 10
    assert "breaking_news" in summary["rss_by_category"]
    assert summary["api_integrations_pending"] >= 5


def test_credibility_from_reliability() -> None:
    feeds = load_crypto_rss_catalog()
    bloomberg = next(f for f in feeds if f.name == "Bloomberg Crypto")
    assert bloomberg.credibility_score >= 0.9
