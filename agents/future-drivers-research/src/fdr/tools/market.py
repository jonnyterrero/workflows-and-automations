"""Tier 2 market data and the deterministic fundamentals arithmetic.

Ratios live here rather than in an agent's head. Margin, leverage, and
free-cash-flow definitions must be identical across every asset and every run,
or cross-asset comparison is meaningless — and a model re-deriving them per
conversation will not be identical.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fdr.config import get_settings

_NOW = datetime.now(tz=UTC)

# Offline fixtures: price, trailing multiples, and where the current multiple
# sits inside its own five-year range. The percentile is what makes
# "expectations already priced in" a measurable claim.
_DEMO_MARKET: dict[str, dict[str, Any]] = {
    "NVDA": {
        "price": 178.4, "market_cap": 4_352_000_000_000,
        "pe_trailing": 44.6, "ev_to_sales": 27.1, "ev_to_ebitda": 38.2,
        "pe_5y_percentile": 0.42, "ev_sales_5y_percentile": 0.71,
        "peer_median_pe": 33.8, "dividend_yield": 0.0002,
    },
    "ETN": {
        "price": 352.1, "market_cap": 138_400_000_000,
        "pe_trailing": 38.8, "ev_to_sales": 5.9, "ev_to_ebitda": 26.4,
        "pe_5y_percentile": 0.88, "ev_sales_5y_percentile": 0.93,
        "peer_median_pe": 27.5, "dividend_yield": 0.0106,
    },
    "SMCI": {
        "price": 41.2, "market_cap": 24_100_000_000,
        "pe_trailing": 21.0, "ev_to_sales": 1.6, "ev_to_ebitda": 18.9,
        "pe_5y_percentile": 0.35, "ev_sales_5y_percentile": 0.44,
        "peer_median_pe": 26.0, "dividend_yield": 0.0,
    },
}


def _f(facts: dict[str, Any], key: str) -> float | None:
    entry = facts.get(key)
    if not isinstance(entry, dict):
        return None
    value = entry.get("value")
    return float(value) if value is not None else None


def _ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return round(numerator / denominator, 4)


def compute_fundamentals(facts: dict[str, Any]) -> dict[str, Any]:
    """Derive ratios from raw XBRL values.

    Every field may be ``None``. A missing value means the company did not
    disclose it, which is information — it is never silently coerced to zero.
    """
    revenue = _f(facts, "revenue")
    gross_profit = _f(facts, "gross_profit")
    operating_income = _f(facts, "operating_income")
    net_income = _f(facts, "net_income")
    assets = _f(facts, "total_assets")
    liabilities = _f(facts, "total_liabilities")
    debt = _f(facts, "long_term_debt")
    cash = _f(facts, "cash")
    ocf = _f(facts, "operating_cash_flow")
    capex = _f(facts, "capex")

    free_cash_flow = None if ocf is None or capex is None else ocf - capex
    equity = None if assets is None or liabilities is None else assets - liabilities
    net_debt = None if debt is None or cash is None else debt - cash

    return {
        "gross_margin": _ratio(gross_profit, revenue),
        "operating_margin": _ratio(operating_income, revenue),
        "net_margin": _ratio(net_income, revenue),
        "return_on_assets": _ratio(net_income, assets),
        "return_on_equity": _ratio(net_income, equity),
        "debt_to_assets": _ratio(debt, assets),
        "debt_to_equity": _ratio(debt, equity),
        "net_debt": net_debt,
        "free_cash_flow": free_cash_flow,
        "fcf_margin": _ratio(free_cash_flow, revenue),
        "cash_conversion": _ratio(ocf, net_income),
        "equity": equity,
        "inputs_present": sorted(k for k in facts if _f(facts, k) is not None),
        "inputs_missing": sorted(k for k in facts if _f(facts, k) is None),
    }


def get_market_snapshot(symbol: str) -> dict[str, Any]:
    """Price and trailing multiples with their own historical percentile. Tier 2."""
    symbol = symbol.upper()
    settings = get_settings()

    if settings.demo_mode:
        row = _DEMO_MARKET.get(symbol)
        if row is None:
            return {"symbol": symbol, "source_tier": 2, "error": "no fixture for symbol"}
        return {
            "symbol": symbol,
            "source_tier": 2,
            "source_name": "market data provider (demo fixture)",
            "as_of": _NOW.isoformat(),
            **row,
            "demo_mode": True,
        }

    if not settings.market_api_key:
        return {
            "symbol": symbol,
            "source_tier": 2,
            "error": "FDR_MARKET_API_KEY unset; cannot fetch live market data",
        }

    # Live market data is provider-specific and licensed. Wire the vendor call
    # here; the contract above is what the agents depend on.
    raise NotImplementedError(
        "Live market provider not configured. Set FDR_DEMO_MODE=true, or implement "
        "the vendor call in fdr.tools.market.get_market_snapshot."
    )


def valuation_context(symbol: str) -> dict[str, Any]:
    """What expectations the current price appears to embed.

    Frames valuation as a percentile against the asset's own history and its
    peers rather than an absolute multiple, because "44x earnings" is not
    interpretable on its own and "richer than 88% of its own five-year history"
    is.
    """
    snapshot = get_market_snapshot(symbol)
    if "error" in snapshot:
        return snapshot

    pe_pct = snapshot.get("pe_5y_percentile")
    ev_pct = snapshot.get("ev_sales_5y_percentile")
    peer_pe = snapshot.get("peer_median_pe")
    pe = snapshot.get("pe_trailing")

    signals: list[str] = []
    if pe_pct is not None and pe_pct >= 0.80:
        signals.append(
            f"Trailing P/E sits in the {pe_pct:.0%} percentile of its own 5-year range."
        )
    if ev_pct is not None and ev_pct >= 0.80:
        signals.append(
            f"EV/Sales sits in the {ev_pct:.0%} percentile of its own 5-year range."
        )
    if pe is not None and peer_pe:
        premium = (pe / peer_pe) - 1.0
        if abs(premium) >= 0.10:
            direction = "premium to" if premium > 0 else "discount to"
            signals.append(f"Trades at a {abs(premium):.0%} {direction} peer median P/E.")

    # Percentiles map to a 0-100 score where cheap scores high. Averaged when
    # both are available so a single distorted multiple cannot dominate.
    percentiles = [p for p in (pe_pct, ev_pct) if p is not None]
    score = round(100.0 * (1.0 - sum(percentiles) / len(percentiles)), 2) if percentiles else 50.0

    return {
        "symbol": symbol.upper(),
        "source_tier": 2,
        "source_name": snapshot.get("source_name"),
        "valuation_score": score,
        "method": "own_history_percentile_and_peer_relative",
        "signals": signals,
        "expectations_summary": (
            " ".join(signals) if signals else "Multiples near their own historical midpoint."
        ),
        "raw": snapshot,
        "demo_mode": snapshot.get("demo_mode", False),
    }
