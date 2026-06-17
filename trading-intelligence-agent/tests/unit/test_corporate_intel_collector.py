"""Unit tests for corporate intelligence scoring heuristics."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

from packages.corporate_intel.collector import CorporateIntelCollector


def _collector() -> CorporateIntelCollector:
    filings_provider = SimpleNamespace(config=SimpleNamespace(name="edgar"))
    return CorporateIntelCollector(None, filings_provider, None)


def test_score_fundamentals_positive_snapshot() -> None:
    collector = _collector()
    score, reasons = collector._score_fundamentals({
        "metrics": {
            "peTTM": 24.0,
            "revenueGrowthTTMYoy": 0.20,
            "epsGrowthTTMYoy": 0.14,
            "netMargin": 0.18,
            "roeTTM": 0.22,
        }
    })
    assert score > 0.4
    assert reasons


def test_score_catalysts_with_surprise_and_recent_filing() -> None:
    collector = _collector()
    today = date.today()
    earnings = [
        {
            "date": (today + timedelta(days=10)).isoformat(),
            "eps_actual": 1.25,
            "eps_estimate": 1.0,
        }
    ]
    filings = [
        {
            "filing_type": "8-K",
            "filed_at": (datetime.now(tz=timezone.utc) - timedelta(days=3)).isoformat(),
        }
    ]
    score, notes, next_earnings = collector._score_catalysts(earnings, filings)
    assert score > 0
    assert next_earnings == earnings[0]["date"]
    assert notes
