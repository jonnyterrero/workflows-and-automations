"""Demo macro provider — realistic fixture macro indicators."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import structlog

from packages.data_providers.base import BaseMacroProvider, ProviderConfig

logger = structlog.get_logger()
_NOW = datetime.now(tz=timezone.utc)


def _monthly(n: int, ref: datetime) -> list[datetime]:
    dates: list[datetime] = []
    cur = ref.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    for _ in range(n):
        dates.append(cur)
        m, y = cur.month - 1, cur.year
        if m == 0:
            m, y = 12, y - 1
        cur = cur.replace(year=y, month=m)
    return list(reversed(dates))


_SPECS: dict[str, tuple[list[float], str, str]] = {
    "fed_funds_rate":     ([5.25, 5.25, 5.25, 5.25, 5.25, 5.25, 5.33, 5.33, 5.40, 5.45, 5.50, 5.50], "monetary_policy", "percent"),
    "cpi_yoy":            ([3.7, 3.5, 3.4, 3.2, 3.1, 3.0, 3.1, 3.2, 3.3, 3.4, 3.4, 3.2], "inflation", "percent"),
    "gdp_growth_qoq":     ([2.1, 2.3, 1.6, 2.0, 2.5, 2.4, 1.9, 1.8, 2.1, 2.2, 2.3, 2.5], "growth", "percent"),
    "unemployment_rate":  ([3.7, 3.7, 3.8, 3.9, 3.9, 4.0, 4.0, 4.1, 4.0, 3.9, 3.8, 3.7], "labor", "percent"),
    "10y_treasury_yield": ([4.20, 4.25, 4.35, 4.50, 4.60, 4.70, 4.75, 4.65, 4.55, 4.48, 4.42, 4.38], "rates", "percent"),
    "2y_treasury_yield":  ([4.55, 4.60, 4.70, 4.80, 4.90, 4.95, 5.00, 4.95, 4.90, 4.85, 4.80, 4.75], "rates", "percent"),
    "vix":                ([14.5, 13.8, 12.5, 13.0, 15.2, 16.8, 17.5, 15.0, 13.5, 12.8, 14.2, 15.0], "volatility", "index"),
    "dxy":                ([103.2, 103.8, 104.1, 104.5, 105.0, 105.5, 105.8, 105.2, 104.8, 104.3, 103.9, 103.5], "forex", "index"),
}


class DemoMacroProvider(BaseMacroProvider):
    def __init__(self) -> None:
        super().__init__(ProviderConfig(name="demo_macro", demo_mode=True))

    async def fetch_indicator(self, series_id: str, limit: int = 12) -> list[dict[str, Any]]:
        if series_id not in _SPECS:
            return []
        values, category, unit = _SPECS[series_id]
        dates = _monthly(12, _NOW)
        n = min(limit, len(values), len(dates))
        return [
            {
                "series_id": series_id,
                "value": values[i],
                "observation_date": dates[i].isoformat(),
                "category": category,
                "unit": unit,
                "source": "demo",
                "fetched_at": _NOW.isoformat(),
            }
            for i in range(n)
        ][-n:]

    async def fetch_yield_curve(self) -> list[dict[str, Any]]:
        maturities = [("3m", 5.28), ("6m", 5.32), ("1y", 5.10), ("2y", 4.75),
                      ("5y", 4.55), ("10y", 4.38), ("30y", 4.52)]
        return [
            {"maturity": mat, "yield_pct": yld,
             "observation_date": _NOW.isoformat(), "source": "demo"}
            for mat, yld in maturities
        ]
