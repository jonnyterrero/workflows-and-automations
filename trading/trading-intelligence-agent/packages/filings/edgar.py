"""SEC EDGAR adapter — public filings with demo mode fallback."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
import structlog
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from packages.data_providers.base import (
    BaseFilingsProvider, ParseError, ProviderConfig, ProviderError, RateLimitConfig,
)

logger = structlog.get_logger()

DEMO_MODE: bool = os.getenv("DEMO_MODE", "false").lower() == "true"
EDGAR_USER_AGENT: str = os.getenv(
    "EDGAR_USER_AGENT", "trading-intelligence-agent/0.1 (dijinvestments3@gmail.com)"
)
_COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
_NOW = datetime.now(tz=timezone.utc)

_DEMO_FILINGS: list[dict[str, Any]] = [
    {
        "company_symbol": "AAPL", "filing_type": "10-Q",
        "filed_at": (_NOW - timedelta(days=45)).isoformat(),
        "url": "https://www.sec.gov/Archives/edgar/data/320193/0000320193-24-000006-index.htm",
        "accession_number": "0000320193-24-000006",
        "text": "Apple Q1 FY2024: Revenue $119.6B (+2% YoY), Services record $23.1B, GM 45.9%.",
        "summary": "Q1 FY2024: Revenue $119.6B, EPS $2.18, Services $23.1B record.",
        "risk_items": [
            "China revenue concentration ~19% amid geopolitical tension",
            "TSMC sole-source dependency for advanced chips",
            "EU Digital Markets Act compliance costs",
        ],
    },
    {
        "company_symbol": "NVDA", "filing_type": "10-Q",
        "filed_at": (_NOW - timedelta(days=30)).isoformat(),
        "url": "https://www.sec.gov/Archives/edgar/data/1045810/0001045810-24-000010-index.htm",
        "accession_number": "0001045810-24-000010",
        "text": "NVIDIA Q4 FY2024: Revenue $22.1B (+265% YoY), Data Center $18.4B (83% of total).",
        "summary": "Q4 FY2024: Revenue $22.1B, Data Center $18.4B, Blackwell architecture announced.",
        "risk_items": [
            "US export controls limit China sales",
            "Top 5 customers ~46% of revenue concentration",
            "TSMC CoWoS packaging sole-source dependency",
            "AMD MI300X / Intel Gaudi / hyperscaler ASICs competition",
        ],
    },
    {
        "company_symbol": "TSLA", "filing_type": "10-Q",
        "filed_at": (_NOW - timedelta(days=60)).isoformat(),
        "url": "https://www.sec.gov/Archives/edgar/data/1318605/0001318605-24-000010-index.htm",
        "accession_number": "0001318605-24-000010",
        "text": "Tesla Q1 2024: Revenue $21.3B (-9% YoY), Auto GM 17.4%, Deliveries 386,810 (-8.5% YoY).",
        "summary": "Q1 2024: Revenue $21.3B (-9%), auto gross margin compressed by pricing.",
        "risk_items": [
            "Price-cut strategy compressing gross margins",
            "BYD surpassed Tesla in global EV sales Q4 2023",
            "NHTSA investigations into Autopilot/FSD",
            "CEO key-person risk with divided attention",
            "Red Sea shipping disruptions at Gigafactory Berlin",
        ],
    },
    {
        "company_symbol": "NVDA", "filing_type": "8-K",
        "filed_at": (_NOW - timedelta(days=5)).isoformat(),
        "url": "https://www.sec.gov/Archives/edgar/data/1045810/0001045810-24-000015-index.htm",
        "accession_number": "0001045810-24-000015",
        "text": "NVIDIA announces 10-for-1 forward stock split effective June 10, 2024.",
        "summary": "10-for-1 stock split announcement.", "risk_items": [],
    },
    {
        "company_symbol": "AAPL", "filing_type": "8-K",
        "filed_at": (_NOW - timedelta(days=10)).isoformat(),
        "url": "https://www.sec.gov/Archives/edgar/data/320193/0000320193-24-000010-index.htm",
        "accession_number": "0000320193-24-000010",
        "text": "Apple announces $0.24/share dividend and $110B share repurchase authorization.",
        "summary": "$0.24/share dividend + $110B buyback.", "risk_items": [],
    },
]


class EDGARFilingsProvider(BaseFilingsProvider):
    def __init__(self) -> None:
        super().__init__(ProviderConfig(
            name="edgar", api_key=None,
            base_url="https://efts.sec.gov/LATEST/search-index",
            rate_limit=RateLimitConfig(requests_per_minute=10, retry_max_attempts=3),
            timeout_seconds=30.0, demo_mode=DEMO_MODE,
        ))
        self._log = logger.bind(provider="edgar")

    async def _headers(self) -> dict[str, str]:
        return {"User-Agent": EDGAR_USER_AGENT, "Accept": "application/json"}

    @retry(
        retry=retry_if_exception_type(ProviderError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, max=30),
        reraise=True,
    )
    async def _resolve_cik(self, symbol: str) -> str | None:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(_COMPANY_TICKERS_URL, headers=await self._headers())
            if response.status_code == 429:
                raise ProviderError("EDGAR rate limit")
            response.raise_for_status()
            data = response.json()

        target = symbol.upper()
        for entry in data.values():
            if str(entry.get("ticker", "")).upper() == target:
                return str(entry.get("cik_str", "")).zfill(10)
        return None

    @retry(
        retry=retry_if_exception_type(ProviderError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, max=30),
        reraise=True,
    )
    async def _fetch_live(
        self, symbol: str, filing_types: list[str], limit: int,
    ) -> list[dict[str, Any]]:
        cik = await self._resolve_cik(symbol)
        if not cik:
            self._log.warning("edgar_cik_not_found", symbol=symbol)
            return []

        url = _SUBMISSIONS_URL.format(cik=cik)
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, headers=await self._headers())
                if response.status_code == 429:
                    raise ProviderError("EDGAR rate limit")
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPStatusError as exc:
                raise ProviderError(f"EDGAR HTTP {exc}") from exc
            except Exception as exc:
                raise ProviderError(f"EDGAR request error: {exc}") from exc

        recent = data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        dates = recent.get("filingDate", [])
        accessions = recent.get("accessionNumber", [])
        primary_docs = recent.get("primaryDocument", [])

        filings: list[dict[str, Any]] = []
        for i, form in enumerate(forms):
            if form not in filing_types:
                continue
            accession = accessions[i].replace("-", "")
            primary = primary_docs[i] if i < len(primary_docs) else ""
            filed_at = dates[i] if i < len(dates) else ""
            doc_url = (
                f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession}/{primary}"
                if primary else f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}"
            )
            filings.append({
                "company_symbol": symbol.upper(),
                "filing_type": form,
                "filed_at": f"{filed_at}T00:00:00+00:00" if filed_at else "",
                "url": doc_url,
                "accession_number": accessions[i] if i < len(accessions) else "",
                "text": "", "summary": "", "risk_items": [],
            })
            if len(filings) >= limit:
                break
        return filings

    async def fetch_recent_filings(
        self, symbol: str, filing_types: list[str] | None = None, limit: int = 10,
    ) -> list[dict[str, Any]]:
        ftypes = filing_types or ["10-K", "10-Q", "8-K"]
        if DEMO_MODE or self.config.demo_mode:
            results = [
                f for f in _DEMO_FILINGS
                if f["company_symbol"].upper() == symbol.upper() and f["filing_type"] in ftypes
            ]
            return results[:limit]
        try:
            return await self._fetch_live(symbol, ftypes, limit)
        except ProviderError as exc:
            self._log.error("edgar_failed", symbol=symbol, error=str(exc))
            return []
