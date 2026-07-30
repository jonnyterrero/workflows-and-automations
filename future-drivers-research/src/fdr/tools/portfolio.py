"""ETF look-through and concentration analysis.

The problem this solves: a portfolio of VOO + QQQM + SMH + NVDA looks
diversified at the ticker level and is a single concentrated semiconductor bet
underneath. Overlap is computed by decomposing every holding into its
underlying names, so the answer is arithmetic rather than intuition.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

# Top-weight holdings per fund. Truncated to the names that drive overlap;
# ``_residual`` absorbs the rest so weights still sum to 1.0 and effective
# exposure is never overstated.
_ETF_HOLDINGS: dict[str, dict[str, float]] = {
    "VOO": {
        "NVDA": 0.074, "AAPL": 0.062, "MSFT": 0.061, "AMZN": 0.038,
        "META": 0.027, "AVGO": 0.025, "GOOGL": 0.021, "TSLA": 0.017,
        "_residual": 0.675,
    },
    "QQQM": {
        "NVDA": 0.091, "AAPL": 0.079, "MSFT": 0.077, "AMZN": 0.055,
        "AVGO": 0.049, "META": 0.038, "TSLA": 0.028, "GOOGL": 0.025,
        "_residual": 0.558,
    },
    "SMH": {
        "NVDA": 0.202, "TSM": 0.111, "AVGO": 0.089, "AMD": 0.052,
        "ASML": 0.048, "QCOM": 0.043, "AMAT": 0.041, "LRCX": 0.036,
        "_residual": 0.378,
    },
    "XLU": {
        "NEE": 0.132, "SO": 0.081, "DUK": 0.076, "CEG": 0.071,
        "AEP": 0.052, "VST": 0.049, "_residual": 0.539,
    },
    "IBIT": {"BTC": 1.0},
    "GLD": {"GOLD": 1.0},
}

# Shared underlying risk drivers. Two tickers with different names can still be
# one bet; this is what catches IBIT + COIN + MSTR.
_RISK_FACTORS: dict[str, str] = {
    "NVDA": "semiconductors", "AVGO": "semiconductors", "AMD": "semiconductors",
    "TSM": "semiconductors", "ASML": "semiconductors", "QCOM": "semiconductors",
    "AMAT": "semiconductors", "LRCX": "semiconductors", "SMCI": "semiconductors",
    "BTC": "crypto_beta", "ETH": "crypto_beta", "COIN": "crypto_beta",
    "MSTR": "crypto_beta", "IBIT": "crypto_beta",
    "NEE": "regulated_power", "SO": "regulated_power", "DUK": "regulated_power",
    "AEP": "regulated_power", "CEG": "merchant_power", "VST": "merchant_power",
    "ETN": "electrical_equipment", "PWR": "electrical_equipment",
    "GOLD": "precious_metals",
}

# Above these shares of the portfolio, flag it.
_NAME_CONCENTRATION_LIMIT = 0.10
_FACTOR_CONCENTRATION_LIMIT = 0.25


def look_through(positions: list[dict[str, Any]]) -> dict[str, float]:
    """Decompose positions into effective underlying weights.

    ``positions`` is ``[{"symbol": "VOO", "weight": 0.4}, ...]`` where weight is
    a share of the total portfolio.
    """
    effective: dict[str, float] = defaultdict(float)
    for position in positions:
        symbol = str(position["symbol"]).upper()
        weight = float(position.get("weight", 0.0))
        if weight <= 0:
            continue
        holdings = _ETF_HOLDINGS.get(symbol)
        if holdings is None:
            effective[symbol] += weight
            continue
        for underlying, share in holdings.items():
            if underlying == "_residual":
                effective[f"{symbol}:other"] += weight * share
            else:
                effective[underlying] += weight * share
    return {k: round(v, 6) for k, v in effective.items()}


def factor_exposures(effective: dict[str, float]) -> dict[str, float]:
    """Aggregate effective weights by shared risk driver."""
    factors: dict[str, float] = defaultdict(float)
    for symbol, weight in effective.items():
        factor = _RISK_FACTORS.get(symbol.upper())
        if factor:
            factors[factor] += weight
    return {k: round(v, 6) for k, v in factors.items()}


def portfolio_overlap(
    positions: list[dict[str, Any]],
    candidate: str,
    candidate_weight: float = 0.05,
) -> dict[str, Any]:
    """How much genuinely new exposure a candidate would add.

    Returns the shape ``AssetDossier.portfolio_overlap`` expects.
    """
    candidate = candidate.upper()
    current = look_through(positions)
    current_factors = factor_exposures(current)

    existing = current.get(candidate, 0.0)
    proposed = look_through(positions + [{"symbol": candidate, "weight": candidate_weight}])
    proposed_factors = factor_exposures(proposed)

    # Only the part of the new position that is not already held counts as new.
    added = max(0.0, proposed.get(candidate, 0.0) - existing)

    overlapping = sorted(
        (sym for sym in proposed if sym in current and not sym.endswith(":other")),
        key=lambda s: -proposed[s],
    )[:10]

    flags: list[str] = []
    if existing > 0:
        flags.append(
            f"Already holds {existing:.1%} of {candidate} indirectly through existing funds."
        )
    post_weight = proposed.get(candidate, 0.0)
    if post_weight > _NAME_CONCENTRATION_LIMIT:
        flags.append(
            f"Post-trade {candidate} would be {post_weight:.1%} of the portfolio, "
            f"above the {_NAME_CONCENTRATION_LIMIT:.0%} single-name limit."
        )

    candidate_factor = _RISK_FACTORS.get(candidate)
    if candidate_factor:
        after = proposed_factors.get(candidate_factor, 0.0)
        before = current_factors.get(candidate_factor, 0.0)
        if after > _FACTOR_CONCENTRATION_LIMIT:
            flags.append(
                f"{candidate_factor.replace('_', ' ').title()} exposure would reach "
                f"{after:.1%} (from {before:.1%}), above the "
                f"{_FACTOR_CONCENTRATION_LIMIT:.0%} factor limit."
            )

    return {
        "candidate": candidate,
        "effective_added_weight": round(added, 6),
        "already_held_indirectly": round(existing, 6),
        "post_trade_weight": round(post_weight, 6),
        "overlapping_holdings": overlapping,
        "concentration_flags": flags,
        "factor_exposures_before": current_factors,
        "factor_exposures_after": proposed_factors,
        "notes": (
            "Effective weights are computed by decomposing every fund into its "
            "underlying holdings, so overlap that is invisible at the ticker "
            "level is counted."
        ),
    }
