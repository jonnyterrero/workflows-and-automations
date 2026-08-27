"""SEC-API.io filings provider."""
from __future__ import annotations

import os
from typing import Any

import httpx
import structlog

from packages.data_providers.base import (
    AuthError,
    BaseFilingsProvider,
    ProviderConfig,
    ProviderError,
    RateLimitConfig,
    RateLimitError,
)

logger = structlog.get_logger()

SEC_API_BASE_URL = "https://api.sec-api.io"


class SecApiFilingsProvider(BaseFilingsProvider):
    """Search recent SEC filings through sec-api.io Query API."""

    def __init__(self, api_key: str | None = None) -> None:
        key = api_key or os.getenv("SEC_API_KEY", "")
        if not key:
            raise AuthError("SEC_API_KEY is required for SecApiFilingsProvider")
        super().__init__(ProviderConfig(
            name="sec_api",
            api_key=key,
            base_url=SEC_API_BASE_URL,
            rate_limit=RateLimitConfig(requests_per_minute=30, retry_max_attempts=3),
            timeout_seconds=30.0,
            demo_mode=False,
        ))
        self._log = logger.bind(provider="sec_api")

    async def fetch_recent_filings(
        self,
        symbol: str,
        filing_types: list[str],
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        forms = " OR ".join(f'formType:"{form_type}"' for form_type in filing_types)
        payload = {
            "query": f'ticker:{symbol.upper().split("-")[0]} AND ({forms})',
            "from": "0",
            "size": str(limit),
            "sort": [{"filedAt": {"order": "desc"}}],
        }
        async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
            try:
                response = await client.post(
                    self.config.base_url,
                    json=payload,
                    headers={
                        "Authorization": self.config.api_key or "",
                        "Content-Type": "application/json",
                    },
                )
            except httpx.RequestError as exc:
                raise ProviderError(f"SEC API request failed: {exc}") from exc

        if response.status_code == 401:
            raise AuthError("SEC API key invalid")
        if response.status_code == 429:
            raise RateLimitError("SEC API rate limit exceeded")
        if response.status_code >= 400:
            raise ProviderError(f"SEC API HTTP {response.status_code}: {response.text[:200]}")

        data = response.json()
        items = data.get("filings") or data.get("data") or []
        filings: list[dict[str, Any]] = []
        for item in items:
            accession = item.get("accessionNo") or item.get("accessionNumber") or ""
            link = item.get("linkToFilingDetails") or item.get("linkToTxt") or item.get("linkToHtml") or ""
            filings.append({
                "company_symbol": symbol.upper().split("-")[0],
                "filing_type": item.get("formType", ""),
                "filed_at": item.get("filedAt", ""),
                "url": f"https://{link.lstrip('/')}" if isinstance(link, str) and link.startswith("sec.gov") else link,
                "accession_number": accession,
                "text": item.get("description", "") or "",
                "summary": item.get("description", "") or "",
                "risk_items": [],
                "source": "sec_api",
            })
        return filings
