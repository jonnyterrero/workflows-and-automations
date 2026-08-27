from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api_service.main import app


@pytest.mark.asyncio
async def test_admin_routes_require_token_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ADMIN_API_TOKEN", "secret-token")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        denied = await client.get("/admin/providers")
        allowed = await client.get("/admin/providers", headers={"X-Admin-Token": "secret-token"})

    assert denied.status_code == 401
    assert allowed.status_code == 200


@pytest.mark.asyncio
async def test_admin_routes_allow_access_without_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ADMIN_API_TOKEN", raising=False)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/admin/providers")

    assert response.status_code == 200
