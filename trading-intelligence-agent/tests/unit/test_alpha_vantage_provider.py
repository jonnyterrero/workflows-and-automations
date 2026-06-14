"""Unit tests for Alpha Vantage market provider (mocked HTTP)."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from packages.data_providers.live.alpha_vantage import AlphaVantageMarketProvider


@pytest.fixture
def av_provider(monkeypatch: pytest.MonkeyPatch) -> AlphaVantageMarketProvider:
    monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "test-av-key")
    return AlphaVantageMarketProvider()


def _mock_response(payload: dict, status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = payload
    return resp


@pytest.mark.asyncio
async def test_fetch_ohlcv_equity(av_provider: AlphaVantageMarketProvider) -> None:
    payload = {
        "Time Series (Daily)": {
            "2024-06-01": {
                "1. open": "190.0", "2. high": "195.0",
                "3. low": "189.0", "4. close": "194.5", "5. volume": "50000000",
            },
            "2024-06-02": {
                "1. open": "194.5", "2. high": "196.0",
                "3. low": "193.0", "4. close": "195.2", "5. volume": "48000000",
            },
        }
    }
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=_mock_response(payload))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("packages.data_providers.live.alpha_vantage.httpx.AsyncClient", return_value=mock_client):
        bars = await av_provider.fetch_ohlcv(
            "AAPL", "1d",
            start=datetime(2024, 6, 1, tzinfo=timezone.utc),
            end=datetime(2024, 6, 3, tzinfo=timezone.utc),
        )

    assert len(bars) == 2
    assert bars[0]["symbol"] == "AAPL"
    assert bars[0]["source"] == "alpha_vantage"
    assert bars[1]["close"] == 195.2


@pytest.mark.asyncio
async def test_fetch_latest_quote(av_provider: AlphaVantageMarketProvider) -> None:
    payload = {
        "Global Quote": {
            "01. symbol": "SPY",
            "02. open": "500.0",
            "03. high": "505.0",
            "04. low": "499.0",
            "05. price": "503.5",
            "06. volume": "80000000",
            "07. latest trading day": "2024-06-01",
        }
    }
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=_mock_response(payload))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("packages.data_providers.live.alpha_vantage.httpx.AsyncClient", return_value=mock_client):
        quote = await av_provider.fetch_latest_quote("SPY")

    assert quote is not None
    assert quote["close"] == 503.5
    assert quote["symbol"] == "SPY"
