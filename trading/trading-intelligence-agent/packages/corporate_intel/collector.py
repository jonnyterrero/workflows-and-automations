"""Corporate fundamentals and filings collector."""
from __future__ import annotations

import time
from datetime import date, datetime, timedelta, timezone
from typing import Any

import structlog

from packages.data_providers.base import BaseFilingsProvider, BaseFundamentalsProvider
from packages.storage.repositories import (
    AssetRepository,
    FilingRepository,
    ModelFeatureRepository,
    RawPayloadRepository,
)

logger = structlog.get_logger()


class CorporateIntelCollector:
    def __init__(
        self,
        fundamentals_provider: BaseFundamentalsProvider | None,
        filings_provider: BaseFilingsProvider,
        db_session_factory: Any,
    ) -> None:
        self.fundamentals_provider = fundamentals_provider
        self.filings_provider = filings_provider
        self.db_factory = db_session_factory
        self._log = logger.bind(
            fundamentals=getattr(fundamentals_provider, "config", None).name if fundamentals_provider else None,
            filings=filings_provider.config.name,
        )

    def _safe_float(self, value: Any) -> float | None:
        try:
            if value is None or value == "":
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    def _score_fundamentals(self, overview: dict[str, Any] | None) -> tuple[float, list[str]]:
        if not overview:
            return 0.0, ["No fundamentals snapshot available"]

        metrics = overview.get("metrics") or {}
        reasons: list[str] = []
        score = 0.0

        pe = self._safe_float(metrics.get("peTTM") or metrics.get("peBasicExclExtraTTM"))
        if pe is not None:
            if 0 < pe <= 30:
                score += 0.12
                reasons.append(f"Valuation reasonable (P/E {pe:.1f})")
            elif pe >= 60:
                score -= 0.12
                reasons.append(f"Valuation stretched (P/E {pe:.1f})")

        rev_growth = self._safe_float(
            metrics.get("revenueGrowthTTMYoy")
            or metrics.get("revenueGrowth3Y")
            or metrics.get("salesGrowthQuarterlyYoy")
        )
        if rev_growth is not None:
            if rev_growth >= 0.12:
                score += 0.20
                reasons.append(f"Revenue growth strong ({rev_growth:.2f})")
            elif rev_growth < 0:
                score -= 0.20
                reasons.append(f"Revenue growth negative ({rev_growth:.2f})")

        eps_growth = self._safe_float(
            metrics.get("epsGrowthTTMYoy")
            or metrics.get("epsGrowth3Y")
            or metrics.get("epsGrowthQuarterlyYoy")
        )
        if eps_growth is not None:
            if eps_growth >= 0.10:
                score += 0.16
                reasons.append(f"EPS growth positive ({eps_growth:.2f})")
            elif eps_growth < 0:
                score -= 0.16
                reasons.append(f"EPS growth negative ({eps_growth:.2f})")

        margin = self._safe_float(
            metrics.get("netMargin")
            or metrics.get("netProfitMarginAnnual")
            or metrics.get("operatingMarginAnnual")
        )
        if margin is not None:
            if margin >= 0.15:
                score += 0.10
                reasons.append(f"Margins healthy ({margin:.2f})")
            elif margin < 0:
                score -= 0.10
                reasons.append(f"Margins negative ({margin:.2f})")

        debt_to_equity = self._safe_float(
            metrics.get("totalDebtToEquityQuarterly")
            or metrics.get("totalDebtToEquityAnnual")
        )
        if debt_to_equity is not None and debt_to_equity > 150:
            score -= 0.08
            reasons.append(f"Leverage elevated (D/E {debt_to_equity:.1f})")

        current_ratio = self._safe_float(metrics.get("currentRatioAnnual") or metrics.get("currentRatioQuarterly"))
        if current_ratio is not None and current_ratio < 1:
            score -= 0.06
            reasons.append(f"Liquidity thin (current ratio {current_ratio:.2f})")

        roe = self._safe_float(metrics.get("roeTTM") or metrics.get("roeAnnual"))
        if roe is not None and roe >= 0.15:
            score += 0.08
            reasons.append(f"Return on equity strong ({roe:.2f})")

        return max(-1.0, min(1.0, round(score, 3))), reasons or ["Neutral fundamentals snapshot"]

    def _score_catalysts(
        self,
        earnings: list[dict[str, Any]],
        filings: list[dict[str, Any]],
    ) -> tuple[float, list[str], str | None]:
        today = date.today()
        score = 0.0
        notes: list[str] = []
        next_earnings: str | None = None

        for event in earnings:
            event_date_raw = event.get("date")
            if not event_date_raw:
                continue
            try:
                event_date = date.fromisoformat(str(event_date_raw))
            except ValueError:
                continue

            if event_date >= today and next_earnings is None:
                next_earnings = event_date.isoformat()
                days_out = (event_date - today).days
                if days_out <= 14:
                    score += 0.05
                    notes.append(f"Earnings in {days_out} days")

            eps_actual = self._safe_float(event.get("eps_actual"))
            eps_est = self._safe_float(event.get("eps_estimate"))
            if eps_actual is not None and eps_est is not None and eps_est != 0:
                surprise = (eps_actual - eps_est) / abs(eps_est)
                if abs(surprise) >= 0.05:
                    score += max(-0.25, min(0.25, surprise))
                    notes.append(f"EPS surprise {surprise:.2f} on {event_date.isoformat()}")

        recent_cutoff = datetime.now(tz=timezone.utc) - timedelta(days=30)
        recent_8k = 0
        recent_reports = 0
        for filing in filings:
            filed_raw = filing.get("filed_at")
            try:
                filed_at = datetime.fromisoformat(str(filed_raw).replace("Z", "+00:00"))
            except ValueError:
                continue
            if filed_at < recent_cutoff:
                continue
            if filing.get("filing_type") == "8-K":
                recent_8k += 1
            elif filing.get("filing_type") in {"10-Q", "10-K"}:
                recent_reports += 1

        if recent_8k:
            score += min(0.10, recent_8k * 0.03)
            notes.append(f"{recent_8k} recent 8-K filings")
        if recent_reports:
            score += min(0.08, recent_reports * 0.04)
            notes.append(f"{recent_reports} recent periodic reports")

        return max(-1.0, min(1.0, round(score, 3))), notes, next_earnings

    async def collect_for_symbols(self, symbols: list[str]) -> dict[str, Any]:
        summary: dict[str, Any] = {}
        equities = [symbol for symbol in symbols if "-USD" not in symbol.upper()]
        async with self.db_factory() as db:
            asset_repo = AssetRepository(db)
            raw_repo = RawPayloadRepository(db)
            feature_repo = ModelFeatureRepository(db)
            filing_repo = FilingRepository(db)

            for symbol in equities:
                t0 = time.monotonic()
                overview = None
                earnings: list[dict[str, Any]] = []
                filings: list[dict[str, Any]] = []
                errors: list[str] = []
                asset = await asset_repo.get_by_symbol(symbol.upper())

                if self.fundamentals_provider is not None:
                    try:
                        overview = await self.fundamentals_provider.fetch_overview(symbol)
                        await raw_repo.store(
                            self.fundamentals_provider.config.name,
                            "fundamentals_overview",
                            symbol,
                            overview or {"symbol": symbol, "metrics": {}},
                        )
                    except Exception as exc:  # noqa: BLE001
                        errors.append(f"overview: {exc}")
                    try:
                        earnings = await self.fundamentals_provider.fetch_earnings(symbol)
                        await raw_repo.store(
                            self.fundamentals_provider.config.name,
                            "earnings_calendar",
                            symbol,
                            {"symbol": symbol, "earnings": earnings},
                        )
                    except Exception as exc:  # noqa: BLE001
                        errors.append(f"earnings: {exc}")

                try:
                    filings = await self.filings_provider.fetch_recent_filings(
                        symbol,
                        ["10-K", "10-Q", "8-K"],
                        limit=8,
                    )
                    await raw_repo.store(
                        self.filings_provider.config.name,
                        "recent_filings",
                        symbol,
                        {"symbol": symbol, "filings": filings},
                    )
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"filings: {exc}")

                filings_upserted = await filing_repo.bulk_upsert(filings)
                fundamental_score, fundamental_notes = self._score_fundamentals(overview)
                catalyst_score, catalyst_notes, next_earnings = self._score_catalysts(earnings, filings)
                features = {
                    "symbol": symbol.upper(),
                    "fundamental_score": fundamental_score,
                    "event_catalyst_score": catalyst_score,
                    "fundamental_notes": fundamental_notes,
                    "catalyst_notes": catalyst_notes,
                    "next_earnings_date": next_earnings,
                    "overview": overview or {},
                    "earnings": earnings[:5],
                    "recent_filing_types": [f.get("filing_type") for f in filings[:5]],
                    "filings_count": len(filings),
                    "source": {
                        "fundamentals": self.fundamentals_provider.config.name if self.fundamentals_provider else None,
                        "filings": self.filings_provider.config.name,
                    },
                }
                await feature_repo.create_snapshot(
                    symbol=symbol.upper(),
                    features_json=features,
                    asset_id=asset.id if asset else None,
                )

                ms = int((time.monotonic() - t0) * 1000)
                self._log.info(
                    "corporate_intel_collected",
                    symbol=symbol.upper(),
                    filings_upserted=filings_upserted,
                    errors=len(errors),
                    ms=ms,
                )
                summary[symbol.upper()] = {
                    "fundamental_score": fundamental_score,
                    "event_catalyst_score": catalyst_score,
                    "next_earnings_date": next_earnings,
                    "filings_fetched": len(filings),
                    "filings_upserted": filings_upserted,
                    "errors": errors,
                }

            if self.fundamentals_provider is not None and hasattr(self.fundamentals_provider, "fetch_ipo_calendar"):
                try:
                    ipos = await self.fundamentals_provider.fetch_ipo_calendar()
                    await raw_repo.store(
                        self.fundamentals_provider.config.name,
                        "ipo_calendar",
                        "upcoming",
                        {"ipos": ipos},
                    )
                    summary["_ipo_calendar"] = {"upcoming_count": len(ipos), "sample": ipos[:5]}
                except Exception as exc:  # noqa: BLE001
                    summary["_ipo_calendar"] = {"upcoming_count": 0, "error": str(exc)}

            await db.commit()
        return summary
