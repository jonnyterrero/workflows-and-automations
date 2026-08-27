"""Unit tests for FRED macro provider (mocked HTTP)."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from packages.data_providers.live.fred import FredMacroProvider


@pytest.fixture
def fred_provider(monkeypatch: pytest.MonkeyPatch) -> FredMacroProvider:
    monkeypatch.setenv("FRED_API_KEY", "test-fred-key")
    return FredMacroProvider()


def _mock_response(payload: dict, status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = payload
    resp.raise_for_status = MagicMock()
    return resp


@pytest.mark.asyncio
async def test_fetch_indicator_fed_funds(fred_provider: FredMacroProvider) -> None:
    payload = {
        "observations": [
            {"date": "2024-02-01", "value": "5.33"},
            {"date": "2024-01-01", "value": "5.25"},
        ]
    }
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=_mock_response(payload))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("packages.data_providers.live.fred.httpx.AsyncClient", return_value=mock_client):
        results = await fred_provider.fetch_indicator("fed_funds_rate", limit=2)

    assert len(results) == 2
    assert results[0]["series_id"] == "fed_funds_rate"
    assert results[0]["source"] == "fred"
    assert results[1]["value"] == 5.33


@pytest.mark.asyncio
async def test_fetch_indicator_cpi_yoy(fred_provider: FredMacroProvider) -> None:
    observations = [
        {"date": f"2023-{m:02d}-01", "value": str(300 + m)}
        for m in range(1, 14)
    ]
    payload = {"observations": observations}
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=_mock_response(payload))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("packages.data_providers.live.fred.httpx.AsyncClient", return_value=mock_client):
        results = await fred_provider.fetch_indicator("cpi_yoy", limit=1)

    assert len(results) >= 1
    assert results[0]["series_id"] == "cpi_yoy"
    assert "value" in results[0]
