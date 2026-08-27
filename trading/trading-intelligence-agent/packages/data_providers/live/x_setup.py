"""X (Twitter) API setup helpers and query builders."""
from __future__ import annotations

import os
from typing import Any
from urllib.parse import unquote

import httpx

X_API_BASE = "https://api.twitter.com/2"
X_DEVELOPER_PORTAL = "https://developer.x.com/en/portal/dashboard"


def normalize_x_bearer_token(raw: str | None = None) -> str:
    """Load and normalize bearer token — handles URL-encoded copies from browser."""
    value = (raw if raw is not None else os.getenv("X_BEARER_TOKEN", "")).strip()
    if not value:
        return ""
    # Browser copy/paste often URL-encodes + and =
    if "%" in value:
        value = unquote(value)
    return value.strip()


def get_x_bearer_token() -> str:
    return normalize_x_bearer_token()


def get_x_config() -> dict[str, Any]:
    bearer = get_x_bearer_token()
    return {
        "configured": bool(bearer),
        "bearer_token_set": bool(bearer),
        "token_url_encoded": "%" in os.getenv("X_BEARER_TOKEN", ""),
        "api_key_set": bool(os.getenv("X_API_KEY", "").strip()),
        "api_secret_set": bool(os.getenv("X_API_SECRET", "").strip()),
        "developer_portal": X_DEVELOPER_PORTAL,
        "required_env": ["X_BEARER_TOKEN"],
        "optional_env": ["X_API_KEY", "X_API_SECRET", "X_CRYPTO_SEARCH_QUERY", "X_EQUITY_SEARCH_QUERY"],
        "setup_steps": [
            "Go to developer.x.com and create a Project + App (Free or Basic tier).",
            "Under Keys and Tokens, generate a Bearer Token (App-only).",
            "Copy the token from the portal dialog — not the browser address bar.",
            "Paste into .env as X_BEARER_TOKEN=... (raw token; + and = are OK).",
            "Restart the API (make run-live) and POST /admin/setup/x/verify to test.",
            "Free tier allows limited recent-search calls — budget is shared across watchlist.",
        ],
        "notes": [
            "Uses official X API v2 recent search only — no scraping.",
            "If verify fails with 401, regenerate Bearer Token in the developer portal.",
            "Crypto queries include $BTC, $ETH, bitcoin, ethereum by default.",
        ],
    }


def build_equity_search_query(symbol: str) -> str:
    custom = os.getenv("X_EQUITY_SEARCH_QUERY", "").strip()
    if custom and "{symbol}" in custom:
        return custom.replace("{symbol}", symbol)
    sym = symbol.upper().replace("-USD", "")
    return f"${sym} OR {sym} -is:retweet lang:en"


def build_crypto_search_query(symbol: str) -> str:
    custom = os.getenv("X_CRYPTO_SEARCH_QUERY", "").strip()
    if custom and "{symbol}" in custom:
        return custom.replace("{symbol}", symbol)
    base = symbol.upper().split("-")[0]
    aliases = {
        "BTC": "bitcoin OR $BTC",
        "ETH": "ethereum OR $ETH",
        "SOL": "solana OR $SOL",
        "BNB": "binance OR $BNB",
        "XRP": "ripple OR $XRP",
        "DOGE": "dogecoin OR $DOGE",
        "ADA": "cardano OR $ADA",
    }
    terms = aliases.get(base, f"${base} OR {base.lower()}")
    return f"({terms}) -is:retweet lang:en"


async def verify_x_bearer(bearer_token: str | None = None) -> dict[str, Any]:
    token = normalize_x_bearer_token(bearer_token)
    if not token:
        return {"ok": False, "error": "X_BEARER_TOKEN not set", "configured": False}

    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            # User lookup is a lighter auth probe; search confirms read access
            user_resp = await client.get(
                f"{X_API_BASE}/users/by/username/X",
                headers=headers,
            )
            if user_resp.status_code in (401, 403):
                detail = user_resp.text[:240]
                return {
                    "ok": False,
                    "configured": True,
                    "error": "Bearer token rejected by X API — regenerate in developer portal",
                    "status_code": user_resp.status_code,
                    "detail": detail,
                    "hint": "Copy Bearer Token from Keys & Tokens dialog, not URL-encoded browser link",
                }

            response = await client.get(
                f"{X_API_BASE}/tweets/search/recent",
                params={"query": "bitcoin lang:en -is:retweet", "max_results": "10"},
                headers=headers,
            )
            if response.status_code == 403:
                return {
                    "ok": False,
                    "configured": True,
                    "error": "Token valid but app lacks recent-search permission — enable Read in app settings",
                    "status_code": 403,
                    "detail": response.text[:240],
                }
            if response.status_code == 429:
                return {
                    "ok": True,
                    "configured": True,
                    "warning": "Rate limited but token appears valid",
                    "status_code": 429,
                }
            if response.status_code in (401,):
                return {
                    "ok": False,
                    "configured": True,
                    "error": "Search endpoint unauthorized — check app tier and Read permissions",
                    "status_code": response.status_code,
                    "detail": response.text[:240],
                }
            response.raise_for_status()
            data = response.json()
            count = len(data.get("data", []))
            return {
                "ok": True,
                "configured": True,
                "status_code": response.status_code,
                "sample_results": count,
                "message": f"X API connected — {count} sample tweets returned",
            }
        except httpx.HTTPError as exc:
            return {"ok": False, "configured": True, "error": str(exc)}
