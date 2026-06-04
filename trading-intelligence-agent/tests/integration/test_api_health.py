"""Integration tests for API health and basic routes."""
from __future__ import annotations

import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

os.environ["DEMO_MODE"] = "true"
os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
os.environ["FIREBASE_PROJECT_ID"] = "demo-trading-intel"

from apps.api_service.main import app
from packages.storage.firebase_db import _init_firebase


@pytest_asyncio.fixture(autouse=True, scope="module")
async def init_firebase():
    """Initialize Firebase emulator connection once for all integration tests."""
    _init_firebase()


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert data["demo_mode"] is True


@pytest.mark.asyncio
async def test_version_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/version")
    assert response.status_code == 200
    assert "version" in response.json()


@pytest.mark.asyncio
async def test_metrics_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/metrics")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_assets_empty_list():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/assets")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_watchlist_empty():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/assets/watchlist")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_news_empty():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/news")
    assert response.status_code == 200
    assert "articles" in response.json()


@pytest.mark.asyncio
async def test_signals_empty():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/signals")
    assert response.status_code == 200
    assert "signals" in response.json()


@pytest.mark.asyncio
async def test_asset_not_found_404():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/assets/NONEXISTENT_TICKER_XYZ")
    assert response.status_code == 404
