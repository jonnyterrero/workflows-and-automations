"""Macro data collector — ingests macroeconomic indicators."""
from __future__ import annotations

import time
from typing import Any

import structlog

from packages.data_providers.base import BaseMacroProvider, ProviderError
from packages.storage.repositories import MacroRepository, RawPayloadRepository

logger = structlog.get_logger()

SERIES_IDS = [
    "fed_funds_rate", "cpi_yoy", "gdp_growth_qoq", "unemployment_rate",
    "10y_treasury_yield", "2y_treasury_yield", "vix", "dxy",
]


class MacroDataCollector:
    def __init__(self, provider: BaseMacroProvider, db_session_factory: Any) -> None:
        self.provider = provider
        self.db_factory = db_session_factory
        self._log = logger.bind(provider=provider.config.name)

    async def collect_all_indicators(self) -> dict[str, Any]:
        summary: dict[str, Any] = {}
        async with self.db_factory() as db:
            raw_repo = RawPayloadRepository(db)
            macro_repo = MacroRepository(db)
            for series_id in SERIES_IDS:
                t0 = time.monotonic()
                try:
                    observations = await self.provider.fetch_indicator(series_id)
                    ms = int((time.monotonic() - t0) * 1000)
                    await raw_repo.store(
                        self.provider.config.name, "macro_indicator", series_id,
                        {"series_id": series_id, "observations": observations},
                    )
                    upserted = await macro_repo.upsert(series_id, observations)
                    self._log.info("macro_collected", series=series_id, obs=len(observations), ms=ms)
                    summary[series_id] = {"observations": len(observations), "upserted": upserted, "error": None}
                except Exception as exc:  # noqa: BLE001
                    ms = int((time.monotonic() - t0) * 1000)
                    self._log.error("macro_failed", series=series_id, error=str(exc), ms=ms)
                    summary[series_id] = {"observations": 0, "upserted": 0, "error": str(exc)}
            await db.commit()
        return summary

    async def collect_yield_curve(self) -> dict[str, Any]:
        t0 = time.monotonic()
        try:
            curve = await self.provider.fetch_yield_curve()
            ms = int((time.monotonic() - t0) * 1000)
            async with self.db_factory() as db:
                raw_repo = RawPayloadRepository(db)
                macro_repo = MacroRepository(db)
                await raw_repo.store(self.provider.config.name, "yield_curve", "yield_curve", {"maturities": curve})
                await macro_repo.upsert("yield_curve", curve)
                await db.commit()
            self._log.info("yield_curve_collected", n=len(curve), ms=ms)
            return {"maturities": len(curve), "error": None}
        except Exception as exc:  # noqa: BLE001
            return {"maturities": 0, "error": str(exc)}

    async def get_macro_context_summary(self, db: Any) -> str:
        macro_repo = MacroRepository(db)

        async def _latest(name: str) -> float | None:
            rows = await macro_repo.get_latest(name, limit=1)
            return float(rows[0]["value"]) if rows else None

        fed = await _latest("fed_funds_rate")
        cpi = await _latest("cpi_yoy")
        t10 = await _latest("10y_treasury_yield")
        t2 = await _latest("2y_treasury_yield")
        vix = await _latest("vix")
        dxy = await _latest("dxy")
        curve = "inverted" if (t2 and t10 and t2 > t10) else "normal"
        parts = [
            f"Fed: {fed:.2f}%" if fed else "Fed: N/A",
            f"CPI: {cpi:.1f}%" if cpi else "CPI: N/A",
            f"10Y: {t10:.2f}%" if t10 else "10Y: N/A",
            f"2Y: {t2:.2f}% ({curve})" if t2 else "2Y: N/A",
            f"VIX: {vix:.1f}" if vix else "VIX: N/A",
            f"DXY: {dxy:.1f}" if dxy else "DXY: N/A",
        ]
        return " | ".join(parts)
