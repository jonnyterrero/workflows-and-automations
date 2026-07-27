"""Tier 1 macro series from FRED (Federal Reserve Bank of St. Louis).

Used by the Theme Scout to establish that a capital-spending or policy cycle is
actually underway, rather than inferring it from reporting about it.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from fdr.config import get_settings

_FRED_URL = "https://api.stlouisfed.org/fred/series/observations"

# Series that bear on the brief's thematic universes.
CURATED_SERIES: dict[str, str] = {
    "FEDFUNDS": "Federal funds effective rate",
    "DGS10": "10-year Treasury constant maturity yield",
    "CPIAUCSL": "CPI, all urban consumers",
    "INDPRO": "Industrial production index",
    "IPUTIL": "Industrial production: electric and gas utilities",
    "NEWORDER": "Manufacturers' new orders: nondefense capital goods ex-aircraft",
    "TTLCONS": "Total construction spending",
}

_NOW = datetime.now(tz=UTC)

_DEMO_SERIES: dict[str, list[tuple[str, float]]] = {
    "FEDFUNDS": [("2026-04-01", 3.88), ("2026-05-01", 3.87), ("2026-06-01", 3.62)],
    "DGS10": [("2026-04-01", 4.21), ("2026-05-01", 4.16), ("2026-06-01", 4.09)],
    "INDPRO": [("2026-04-01", 103.4), ("2026-05-01", 103.9), ("2026-06-01", 104.6)],
    "IPUTIL": [("2026-04-01", 99.8), ("2026-05-01", 101.7), ("2026-06-01", 103.9)],
    "NEWORDER": [("2026-04-01", 74_100.0), ("2026-05-01", 74_950.0), ("2026-06-01", 76_300.0)],
    "TTLCONS": [("2026-04-01", 2_180_000.0), ("2026-05-01", 2_196_000.0), ("2026-06-01", 2_214_000.0)],
    "CPIAUCSL": [("2026-04-01", 322.4), ("2026-05-01", 323.1), ("2026-06-01", 323.8)],
}


def fred_series(series_id: str, observations: int = 12) -> dict[str, Any]:
    """Recent observations for a FRED series, with trend. Tier 1."""
    series_id = series_id.upper()
    settings = get_settings()

    if settings.demo_mode:
        rows = _DEMO_SERIES.get(series_id)
        if rows is None:
            return {
                "series_id": series_id,
                "source_tier": 1,
                "error": f"no fixture for series; available: {sorted(_DEMO_SERIES)}",
            }
        points = [{"date": d, "value": v} for d, v in rows][-observations:]
        return _with_trend(series_id, points, "FRED (demo fixture)", demo=True)

    if not settings.fred_api_key:
        return {"series_id": series_id, "source_tier": 1, "error": "FRED_API_KEY unset"}

    start = (_NOW - timedelta(days=365 * 3)).date().isoformat()
    with httpx.Client(timeout=settings.http_timeout_seconds) as client:
        response = client.get(
            _FRED_URL,
            params={
                "series_id": series_id,
                "api_key": settings.fred_api_key,
                "file_type": "json",
                "observation_start": start,
            },
        )
        response.raise_for_status()
        raw = response.json().get("observations", [])

    points = [
        {"date": row["date"], "value": float(row["value"])}
        for row in raw
        if row.get("value") not in (None, ".", "")
    ][-observations:]
    return _with_trend(series_id, points, "FRED", demo=False)


def _with_trend(
    series_id: str, points: list[dict[str, Any]], source_name: str, demo: bool
) -> dict[str, Any]:
    change_pct = None
    direction = "flat"
    if len(points) >= 2 and points[0]["value"]:
        change_pct = round((points[-1]["value"] / points[0]["value"] - 1.0) * 100.0, 2)
        if change_pct > 0.5:
            direction = "rising"
        elif change_pct < -0.5:
            direction = "falling"

    return {
        "series_id": series_id,
        "title": CURATED_SERIES.get(series_id, series_id),
        "source_tier": 1,
        "source_name": source_name,
        "source_url": f"https://fred.stlouisfed.org/series/{series_id}",
        "observations": points,
        "latest": points[-1] if points else None,
        "change_pct_over_window": change_pct,
        "direction": direction,
        "demo_mode": demo,
    }
