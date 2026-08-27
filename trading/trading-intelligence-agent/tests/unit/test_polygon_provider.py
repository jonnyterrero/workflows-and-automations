"""Unit tests for Polygon market provider (mocked HTTP)."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from packages.data_providers.live.polygon_market import PolygonMarketProvider


@pytest.fixture
def polygon_provider(monkeypatch: pytest.MonkeyPatch) -> PolygonMarketProvider:
    monkeypatch.setenv("POLYGON_API_KEY", "test-poly-key")
    return PolygonMarketProvider()


def _mock_response(payload: dict, status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = payload
    resp.text = str(payload)
    return resp


@pytest.mark.asyncio
async def test_fetch_ohlcv_daily_bars(polygon_provider: PolygonMarketProvider) -> None:
    payload = {
        "status": "OK",
        "results": [
            {"t": 1717200000000, "o": 190.0, "h": 195.0, "l": 189.0, "c": 194.5, "v": 50000000},
            {"t": 1717286400000, "o": 194.5, "h": 196.0, "l": 193.0, "c": 195.2, "v": 48000000},
        ],
    }
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=_mock_response(payload))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("packages.data_providers.live.polygon_market.httpx.AsyncClient", return_value=mock_client):
        bars = await polygon_provider.fetch_ohlcv(
            "AAPL",
            "1d",
            start=datetime(2024, 6, 1, tzinfo=timezone.utc),
            end=datetime(2024, 6, 3, tzinfo=timezone.utc),
        )

    assert len(bars) == 2
    assert bars[0]["symbol"] == "AAPL"
    assert bars[1]["close"] == 195.2
    assert bars[0]["source"] == "polygon"


@pytest.mark.asyncio
async def test_fetch_latest_quote_open_close(polygon_provider: PolygonMarketProvider) -> None:
    payload = {
        "status": "OK",
        "from": "2024-06-03",
        "open": 500.0,
        "high": 505.0,
        "low": 499.0,
        "close": 503.5,
        "volume": 80000000,
    }
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=_mock_response(payload))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("packages.data_providers.live.polygon_market.httpx.AsyncClient", return_value=mock_client):
        quote = await polygon_provider.fetch_latest_quote("SPY")

    assert quote is not None
    assert quote["symbol"] == "SPY"
    assert quote["close"] == 503.5
    assert quote["source"] == "polygon"
