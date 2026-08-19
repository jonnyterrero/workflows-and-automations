"""Unit tests for Finnhub and SEC API providers (mocked HTTP)."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from packages.data_providers.live.finnhub_fundamentals import FinnhubFundamentalsProvider
from packages.data_providers.live.finnhub_news import FinnhubNewsProvider
from packages.data_providers.live.sec_api_filings import SecApiFilingsProvider


def _mock_response(payload: object, status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = payload
    resp.text = str(payload)
    return resp


@pytest.fixture
def finnhub_news(monkeypatch: pytest.MonkeyPatch) -> FinnhubNewsProvider:
    monkeypatch.setenv("FINNHUB_API_KEY", "test-fh-key")
    return FinnhubNewsProvider()


@pytest.fixture
def finnhub_fundamentals(monkeypatch: pytest.MonkeyPatch) -> FinnhubFundamentalsProvider:
    monkeypatch.setenv("FINNHUB_API_KEY", "test-fh-key")
    return FinnhubFundamentalsProvider()


@pytest.fixture
def sec_api(monkeypatch: pytest.MonkeyPatch) -> SecApiFilingsProvider:
    monkeypatch.setenv("SEC_API_KEY", "test-sec-key")
    return SecApiFilingsProvider()


@pytest.mark.asyncio
async def test_finnhub_company_news(finnhub_news: FinnhubNewsProvider) -> None:
    payload = [
        {
            "headline": "Apple supplier demand improves",
            "url": "https://example.test/apple-news",
            "datetime": 1717362000,
            "summary": "Demand improved across the quarter.",
            "source": "Reuters",
        }
    ]
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=_mock_response(payload))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("packages.data_providers.live.finnhub_news.httpx.AsyncClient", return_value=mock_client):
        articles = await finnhub_news.fetch_articles("AAPL", limit=5, hours_back=48)

    assert len(articles) == 1
    assert articles[0]["source"] == "Reuters"
    assert articles[0]["credibility_score"] >= 0.7


@pytest.mark.asyncio
async def test_finnhub_overview_and_earnings(finnhub_fundamentals: FinnhubFundamentalsProvider) -> None:
    overview_payload = {
        "metricType": "all",
        "metric": {"peTTM": 25.0, "revenueGrowthTTMYoy": 0.18, "roeTTM": 0.21},
        "series": {},
    }
    earnings_payload = {
        "earningsCalendar": [
            {
                "date": "2026-07-25",
                "epsActual": 1.25,
                "epsEstimate": 1.10,
                "revenueActual": 100.0,
                "revenueEstimate": 95.0,
            }
        ]
    }
    ipo_payload = {
        "ipoCalendar": [
            {"date": "2026-07-01", "name": "Example IPO", "symbol": "EXM", "exchange": "NASDAQ"}
        ]
    }
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=[
        _mock_response(overview_payload),
        _mock_response(earnings_payload),
        _mock_response(ipo_payload),
    ])
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("packages.data_providers.live.finnhub_fundamentals.httpx.AsyncClient", return_value=mock_client):
        overview = await finnhub_fundamentals.fetch_overview("AAPL")
        earnings = await finnhub_fundamentals.fetch_earnings("AAPL")
        ipos = await finnhub_fundamentals.fetch_ipo_calendar()

    assert overview is not None
    assert overview["metrics"]["peTTM"] == 25.0
    assert earnings[0]["eps_actual"] == 1.25
    assert ipos[0]["symbol"] == "EXM"


@pytest.mark.asyncio
async def test_sec_api_recent_filings(sec_api: SecApiFilingsProvider) -> None:
    payload = {
        "filings": [
            {
                "accessionNo": "0000950170-24-048288",
                "formType": "10-Q",
                "filedAt": "2024-04-25T16:06:24-04:00",
                "ticker": "MSFT",
                "linkToFilingDetails": "sec.gov/Archives/edgar/data/789019/000095017024048288/msft-20240331.htm",
                "description": "Quarterly report",
            }
        ]
    }
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=_mock_response(payload))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("packages.data_providers.live.sec_api_filings.httpx.AsyncClient", return_value=mock_client):
        filings = await sec_api.fetch_recent_filings("MSFT", ["10-Q"], limit=2)

    assert len(filings) == 1
    assert filings[0]["filing_type"] == "10-Q"
    assert filings[0]["company_symbol"] == "MSFT"
    assert filings[0]["url"].startswith("https://sec.gov/")
