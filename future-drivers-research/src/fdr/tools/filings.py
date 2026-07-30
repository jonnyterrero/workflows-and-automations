"""Tier 1 filings access via SEC EDGAR.

These are the facts the Evidence Analyst is allowed to build on. Everything
returned here carries ``source_tier: 1``.

The agent never calls SEC directly — it asks us, and we make the request with
the orchestrator's user agent. That keeps rate-limit identity and contact
details under our control rather than the sandbox's.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from fdr.config import get_settings

_COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
_COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

# XBRL tags vary by filer; try in order of preference.
_FACT_TAGS: dict[str, list[str]] = {
    "revenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
    ],
    "net_income": ["NetIncomeLoss"],
    "operating_income": ["OperatingIncomeLoss"],
    "gross_profit": ["GrossProfit"],
    "total_assets": ["Assets"],
    "total_liabilities": ["Liabilities"],
    "long_term_debt": ["LongTermDebtNoncurrent", "LongTermDebt"],
    "cash": ["CashAndCashEquivalentsAtCarryingValue"],
    "shares_outstanding": [
        "CommonStockSharesOutstanding",
        "WeightedAverageNumberOfDilutedSharesOutstanding",
    ],
    "operating_cash_flow": ["NetCashProvidedByUsedInOperatingActivities"],
    "capex": ["PaymentsToAcquirePropertyPlantAndEquipment"],
}

_NOW = datetime.now(tz=UTC)

# Offline fixtures. Deliberately include a company whose theme exposure is
# talked about more than it is disclosed, so the "exposure not proven" path is
# exercised rather than merely implemented.
_DEMO_FILINGS: dict[str, list[dict[str, Any]]] = {
    "NVDA": [
        {
            "form": "10-Q",
            "filed_at": (_NOW - timedelta(days=28)).isoformat(),
            "accession": "0001045810-26-000012",
            "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001045810",
            "summary": (
                "Data Center revenue $30.8B of $35.1B total (87.7%). Management "
                "attributes growth to accelerated computing and networking demand. "
                "Top four customers represent 41% of revenue."
            ),
        },
    ],
    "ETN": [
        {
            "form": "10-K",
            "filed_at": (_NOW - timedelta(days=120)).isoformat(),
            "accession": "0001551182-26-000008",
            "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001551182",
            "summary": (
                "Electrical Americas segment revenue $11.0B, +12% organic, driven by "
                "data-center and utility capital spending. Backlog up 28% year over "
                "year; twelve-month backlog coverage disclosed at 1.4x."
            ),
        },
    ],
    "SMCI": [
        {
            "form": "10-K",
            "filed_at": (_NOW - timedelta(days=300)).isoformat(),
            "accession": "0000950170-26-000044",
            "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001375365",
            "summary": (
                "Discusses AI infrastructure opportunity qualitatively. Does not "
                "disaggregate AI-attributable revenue. Gross margin 11.3%, down "
                "from 18.0%. Two customers exceed 10% of revenue each."
            ),
        },
    ],
}

_DEMO_FACTS: dict[str, dict[str, float]] = {
    "NVDA": {
        "revenue": 35_100_000_000, "net_income": 19_300_000_000,
        "operating_income": 21_900_000_000, "gross_profit": 26_200_000_000,
        "total_assets": 96_000_000_000, "total_liabilities": 30_100_000_000,
        "long_term_debt": 8_460_000_000, "cash": 9_100_000_000,
        "shares_outstanding": 24_400_000_000,
        "operating_cash_flow": 17_600_000_000, "capex": 1_200_000_000,
    },
    "ETN": {
        "revenue": 24_900_000_000, "net_income": 3_570_000_000,
        "operating_income": 4_450_000_000, "gross_profit": 9_200_000_000,
        "total_assets": 38_600_000_000, "total_liabilities": 18_100_000_000,
        "long_term_debt": 8_200_000_000, "cash": 2_300_000_000,
        "shares_outstanding": 393_000_000,
        "operating_cash_flow": 4_300_000_000, "capex": 750_000_000,
    },
    "SMCI": {
        "revenue": 14_900_000_000, "net_income": 1_150_000_000,
        "operating_income": 1_220_000_000, "gross_profit": 1_680_000_000,
        "total_assets": 9_900_000_000, "total_liabilities": 4_700_000_000,
        "long_term_debt": 1_900_000_000, "cash": 1_670_000_000,
        "shares_outstanding": 586_000_000,
        "operating_cash_flow": -2_500_000_000, "capex": 200_000_000,
    },
}


def _client() -> httpx.Client:
    settings = get_settings()
    return httpx.Client(
        timeout=settings.http_timeout_seconds,
        headers={"User-Agent": settings.edgar_user_agent, "Accept-Encoding": "gzip, deflate"},
    )


def _resolve_cik(symbol: str, client: httpx.Client) -> str | None:
    response = client.get(_COMPANY_TICKERS_URL)
    response.raise_for_status()
    for row in response.json().values():
        if row.get("ticker", "").upper() == symbol.upper():
            return str(row["cik_str"]).zfill(10)
    return None


def _latest_fact(facts: dict[str, Any], tags: list[str]) -> tuple[float, str] | None:
    """Most recent annual/quarterly value for the first tag that resolves."""
    us_gaap = facts.get("facts", {}).get("us-gaap", {})
    for tag in tags:
        entry = us_gaap.get(tag)
        if not entry:
            continue
        candidates: list[dict[str, Any]] = []
        for unit_rows in entry.get("units", {}).values():
            candidates.extend(unit_rows)
        dated = [row for row in candidates if row.get("end") and row.get("val") is not None]
        if not dated:
            continue
        newest = max(dated, key=lambda r: r["end"])
        return float(newest["val"]), str(newest["end"])
    return None


def sec_recent_filings(symbol: str, forms: list[str] | None = None, limit: int = 5) -> dict[str, Any]:
    """Recent filings for a ticker. Tier 1."""
    symbol = symbol.upper()
    wanted = {f.upper() for f in (forms or ["10-K", "10-Q", "8-K"])}
    settings = get_settings()

    if settings.demo_mode:
        rows = [f for f in _DEMO_FILINGS.get(symbol, []) if f["form"].upper() in wanted]
        return {
            "symbol": symbol,
            "source_tier": 1,
            "source_name": "SEC EDGAR (demo fixture)",
            "filings": rows[:limit],
            "demo_mode": True,
        }

    with _client() as client:
        cik = _resolve_cik(symbol, client)
        if cik is None:
            return {"symbol": symbol, "source_tier": 1, "error": "ticker not found in SEC index"}

        response = client.get(_SUBMISSIONS_URL.format(cik=cik))
        response.raise_for_status()
        recent = response.json().get("filings", {}).get("recent", {})

        rows: list[dict[str, Any]] = []
        for form, filed, accession, doc in zip(
            recent.get("form", []),
            recent.get("filingDate", []),
            recent.get("accessionNumber", []),
            recent.get("primaryDocument", []),
            strict=False,
        ):
            if form.upper() not in wanted:
                continue
            plain = accession.replace("-", "")
            rows.append(
                {
                    "form": form,
                    "filed_at": filed,
                    "accession": accession,
                    "url": (
                        f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{plain}/{doc}"
                    ),
                }
            )
            if len(rows) >= limit:
                break

        return {
            "symbol": symbol,
            "cik": cik,
            "source_tier": 1,
            "source_name": "SEC EDGAR",
            "filings": rows,
            "demo_mode": False,
        }


def sec_company_facts(symbol: str) -> dict[str, Any]:
    """Structured XBRL fundamentals. Tier 1.

    Returns raw reported values only. Ratios are computed in
    ``fdr.tools.market.compute_fundamentals`` so the arithmetic is testable and
    identical across every asset, rather than re-derived per conversation.
    """
    symbol = symbol.upper()
    settings = get_settings()

    if settings.demo_mode:
        values = _DEMO_FACTS.get(symbol)
        if values is None:
            return {"symbol": symbol, "source_tier": 1, "error": "no fixture for symbol"}
        return {
            "symbol": symbol,
            "source_tier": 1,
            "source_name": "SEC EDGAR XBRL companyfacts (demo fixture)",
            "as_of": (_NOW - timedelta(days=30)).date().isoformat(),
            "facts": {k: {"value": v, "period_end": None} for k, v in values.items()},
            "demo_mode": True,
        }

    with _client() as client:
        cik = _resolve_cik(symbol, client)
        if cik is None:
            return {"symbol": symbol, "source_tier": 1, "error": "ticker not found in SEC index"}

        response = client.get(_COMPANY_FACTS_URL.format(cik=cik))
        response.raise_for_status()
        payload = response.json()

    resolved: dict[str, Any] = {}
    for name, tags in _FACT_TAGS.items():
        found = _latest_fact(payload, tags)
        if found is not None:
            value, period_end = found
            resolved[name] = {"value": value, "period_end": period_end}

    return {
        "symbol": symbol,
        "cik": cik,
        "source_tier": 1,
        "source_name": "SEC EDGAR XBRL companyfacts",
        "entity_name": payload.get("entityName"),
        "facts": resolved,
        "demo_mode": False,
    }
