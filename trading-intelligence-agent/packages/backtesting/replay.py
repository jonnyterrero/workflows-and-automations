"""Signal replay and basic backtesting.

IMPORTANT: All metrics here are experimental. Backtesting has limitations:
- Survivorship bias
- Look-ahead bias (mitigated by using signal creation timestamp)
- Market impact / slippage not modeled
- Past performance does not predict future results
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np
import structlog

from packages.storage.repositories import MarketPriceRepository, SignalRepository

logger = structlog.get_logger()

DISCLAIMER = (
    "EXPERIMENTAL — Backtesting results are subject to survivorship bias, "
    "lookahead contamination, and market impact not being modeled. "
    "Past signal performance does not predict future returns. "
    "This is NOT financial advice."
)


class SignalReplayer:
    """Replay historical signals against stored price data."""

    def __init__(self, db_session_factory: Any) -> None:
        self.db_factory = db_session_factory

    async def replay_asset(
        self,
        asset_id: int,
        symbol: str,
        lookforward_days: int = 5,
        signal_limit: int = 100,
    ) -> dict[str, Any]:
        """
        For each stored signal for asset_id, look up the price n days later
        and measure the return. Returns aggregate metrics.

        Strict anti-lookahead: only use prices AFTER signal.created_at.
        """
        async with self.db_factory() as db:
            signal_repo = SignalRepository(db)
            price_repo = MarketPriceRepository(db)

            signals = await signal_repo.get_by_asset(asset_id, limit=signal_limit)
            if not signals:
                return {"symbol": symbol, "signal_count": 0, "error": "No signals found", "disclaimer": DISCLAIMER}

            results: list[dict[str, Any]] = []
            for sig in signals:
                sig_ts = sig.created_at or sig.timestamp
                if not sig_ts:
                    continue
                if not sig_ts.tzinfo:
                    sig_ts = sig_ts.replace(tzinfo=timezone.utc)

                # Entry: first price strictly AFTER signal creation (no lookahead)
                entry_start = sig_ts + timedelta(minutes=1)
                entry_end = sig_ts + timedelta(days=2)
                entry_prices = await price_repo.get_range(asset_id, entry_start, entry_end)
                if not entry_prices:
                    continue
                entry_price = entry_prices[0].close

                # Exit: price lookforward_days after entry
                exit_start = entry_start + timedelta(days=lookforward_days - 1)
                exit_end = entry_start + timedelta(days=lookforward_days + 2)
                exit_prices = await price_repo.get_range(asset_id, exit_start, exit_end)
                if not exit_prices:
                    continue
                exit_price = exit_prices[-1].close

                if entry_price <= 0:
                    continue

                ret = (exit_price - entry_price) / entry_price
                direction = sig.direction or "neutral"
                aligned = (
                    (direction == "bullish" and ret > 0)
                    or (direction == "bearish" and ret < 0)
                )
                results.append({
                    "signal_id": sig.id,
                    "direction": direction,
                    "score": sig.score,
                    "confidence": sig.confidence,
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "return": round(ret, 5),
                    "aligned": aligned,
                    "signal_ts": sig_ts.isoformat(),
                })

        if not results:
            return {"symbol": symbol, "signal_count": 0, "error": "No price data for signals", "disclaimer": DISCLAIMER}

        returns = [r["return"] for r in results]
        aligned_count = sum(1 for r in results if r["aligned"])
        arr = np.array(returns)
        max_drawdown = _max_drawdown(arr)
        sharpe = _sharpe(arr)

        return {
            "symbol": symbol,
            "signal_count": len(results),
            "lookforward_days": lookforward_days,
            "win_rate": round(aligned_count / len(results), 3),
            "avg_return": round(float(np.mean(arr)), 4),
            "median_return": round(float(np.median(arr)), 4),
            "max_return": round(float(np.max(arr)), 4),
            "min_return": round(float(np.min(arr)), 4),
            "max_drawdown": round(max_drawdown, 4),
            "volatility": round(float(np.std(arr)), 4),
            "sharpe_estimate": round(sharpe, 3),
            "false_positive_rate": round(1 - aligned_count / len(results), 3),
            "results": results[-20:],
            "disclaimer": DISCLAIMER,
        }


def _max_drawdown(returns: np.ndarray) -> float:
    if len(returns) == 0:
        return 0.0
    cumulative = np.cumprod(1 + returns)
    running_max = np.maximum.accumulate(cumulative)
    drawdowns = (cumulative - running_max) / running_max
    return float(np.min(drawdowns))


def _sharpe(returns: np.ndarray, periods_per_year: int = 252) -> float:
    if len(returns) < 2 or float(np.std(returns)) == 0:
        return 0.0
    return float(np.mean(returns) / np.std(returns) * np.sqrt(periods_per_year))
