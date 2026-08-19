"""Optional admin route protection for public deployments."""
from __future__ import annotations

import os
import secrets

from fastapi import Header, HTTPException, status


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


async def require_admin_api_token(
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
    authorization: str | None = Header(default=None),
) -> None:
    expected = os.getenv("ADMIN_API_TOKEN", "").strip()
    if not expected:
        return

    provided = (x_admin_token or _extract_bearer_token(authorization) or "").strip()
    if provided and secrets.compare_digest(provided, expected):
        return

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Admin API token required",
        headers={"WWW-Authenticate": "Bearer"},
    )
