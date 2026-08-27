"""Unit tests for Coinbase Exchange crypto provider (mocked HTTP)."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from packages.data_providers.live.coinbase_exchange import CoinbaseExchangeCryptoProvider


def _mock_response(payload: object, status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = payload
    resp.text = str(payload)
    return resp


@pytest.mark.asyncio
async def test_fetch_ohlcv_coinbase() -> None:
    provider = CoinbaseExchangeCryptoProvider()
    payload = [
        [1717286400, 65300.03, 66944.0, 66276.79, 65616.64, 6347.81],
        [1717372800, 64491.88, 66384.01, 65616.64, 64786.73, 5688.54],
    ]
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=_mock_response(payload))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("packages.data_providers.live.coinbase_exchange.httpx.AsyncClient", return_value=mock_client):
        bars = await provider.fetch_ohlcv("BTC-USD", limit=2)

    assert len(bars) == 2
    assert bars[0]["symbol"] == "BTC-USD"
    assert bars[1]["close"] == 64786.73
    assert bars[0]["source"] == "coinbase_exchange"


@pytest.mark.asyncio
async def test_fetch_ticker_and_order_book_coinbase() -> None:
    provider = CoinbaseExchangeCryptoProvider()
    ticker_payload = {
        "ask": "64449.66",
        "bid": "64447.68",
        "volume": "6640.9613448",
        "price": "64447.65",
        "time": "2026-06-17T19:30:10.591580174Z",
    }
    book_payload = {
        "bids": [["64450.01", "0.00101293", 1], ["64449.59", "0.00101293", 1]],
        "asks": [["64450.10", "0.05101293", 1], ["64450.12", "0.02101293", 1]],
    }
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=[
        _mock_response(ticker_payload),
        _mock_response(book_payload),
    ])
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("packages.data_providers.live.coinbase_exchange.httpx.AsyncClient", return_value=mock_client):
        ticker = await provider.fetch_ticker("BTC-USD")
        book = await provider.fetch_order_book("BTC-USD", depth=1)

    assert ticker is not None
    assert ticker["bid"] == 64447.68
    assert ticker["source"] == "coinbase_exchange"
    assert book is not None
    assert len(book["bids"]) == 1
    assert book["asks"][0]["price"] == 64450.10
