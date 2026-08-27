"""Technical analysis calculations using numpy/pandas only."""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


class TechnicalAnalyzer:
    def compute(self, prices: list[dict[str, Any]]) -> dict[str, Any]:
        if not prices:
            return self._empty()
        closes = [float(p.get("close", 0) or 0) for p in prices]
        highs = [float(p.get("high", 0) or 0) for p in prices]
        lows = [float(p.get("low", 0) or 0) for p in prices]
        n = len(closes)
        latest = closes[-1] if closes else 0.0

        sma20 = self._sma(closes, 20)
        sma50 = self._sma(closes, 50)
        sma200 = self._sma(closes, 200)
        ema12 = self._ema(closes, 12)
        ema26 = self._ema(closes, 26)
        rsi = self._rsi(closes)
        macd, macd_sig, macd_hist = self._macd(closes)
        bb_up, bb_low, bb_width = self._bollinger(closes)
        atr = self._atr(highs, lows, closes)
        vol20 = self._vol(closes, 20)
        vol5 = self._vol(closes, 5)
        trend = self.compute_trend(sma20, sma50, sma200, latest)
        momentum = self.compute_momentum_score(rsi, macd, macd_sig, trend)
        technical_signal = "bullish" if momentum > 0.2 else ("bearish" if momentum < -0.2 else "neutral")

        return {
            "latest_close": round(latest, 4),
            "sma_20": round(sma20, 4) if sma20 else None,
            "sma_50": round(sma50, 4) if sma50 else None,
            "sma_200": round(sma200, 4) if sma200 else None,
            "ema_12": round(ema12, 4) if ema12 else None,
            "ema_26": round(ema26, 4) if ema26 else None,
            "rsi_14": round(rsi, 2) if rsi else None,
            "macd": round(macd, 4) if macd else None,
            "macd_signal": round(macd_sig, 4) if macd_sig else None,
            "macd_hist": round(macd_hist, 4) if macd_hist else None,
            "bb_upper": round(bb_up, 4) if bb_up else None,
            "bb_lower": round(bb_low, 4) if bb_low else None,
            "bb_width": round(bb_width, 4) if bb_width else None,
            "atr_14": round(atr, 4) if atr else None,
            "vol_20d": round(vol20, 4) if vol20 else None,
            "vol_5d": round(vol5, 4) if vol5 else None,
            "trend_direction": trend,
            "momentum_score": round(momentum, 3),
            "technical_signal": technical_signal,
            "data_points": n,
        }

    def _empty(self) -> dict[str, Any]:
        return {k: None for k in [
            "latest_close", "sma_20", "sma_50", "sma_200", "ema_12", "ema_26",
            "rsi_14", "macd", "macd_signal", "macd_hist", "bb_upper", "bb_lower",
            "bb_width", "atr_14", "vol_20d", "vol_5d",
        ]} | {"trend_direction": "sideways", "momentum_score": 0.0,
               "technical_signal": "neutral", "data_points": 0}

    def _sma(self, closes: list[float], period: int) -> float | None:
        if len(closes) < period:
            return None
        return float(np.mean(closes[-period:]))

    def _ema(self, closes: list[float], period: int) -> float | None:
        if len(closes) < period:
            return None
        s = pd.Series(closes)
        return float(s.ewm(span=period, adjust=False).mean().iloc[-1])

    def _rsi(self, closes: list[float], period: int = 14) -> float | None:
        if len(closes) < period + 1:
            return None
        arr = np.array(closes)
        deltas = np.diff(arr)
        gains = np.where(deltas > 0, deltas, 0.0)
        losses = np.where(deltas < 0, -deltas, 0.0)
        avg_gain = float(np.mean(gains[-period:]))
        avg_loss = float(np.mean(losses[-period:]))
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    def _macd(self, closes: list[float]) -> tuple[float | None, float | None, float | None]:
        if len(closes) < 26:
            return None, None, None
        ema12 = self._ema(closes, 12)
        ema26 = self._ema(closes, 26)
        if ema12 is None or ema26 is None:
            return None, None, None
        macd_val = ema12 - ema26
        s = pd.Series(closes)
        macd_series = s.ewm(span=12, adjust=False).mean() - s.ewm(span=26, adjust=False).mean()
        if len(macd_series) < 9:
            return macd_val, None, None
        signal = float(macd_series.ewm(span=9, adjust=False).mean().iloc[-1])
        hist = macd_val - signal
        return macd_val, signal, hist

    def _bollinger(
        self, closes: list[float], period: int = 20, n_std: float = 2.0,
    ) -> tuple[float | None, float | None, float | None]:
        if len(closes) < period:
            return None, None, None
        window = closes[-period:]
        mean = float(np.mean(window))
        std = float(np.std(window))
        upper = mean + n_std * std
        lower = mean - n_std * std
        width = (upper - lower) / mean if mean != 0 else 0.0
        return upper, lower, width

    def _atr(
        self, highs: list[float], lows: list[float], closes: list[float], period: int = 14,
    ) -> float | None:
        if len(closes) < period + 1:
            return None
        trs = []
        for i in range(1, len(closes)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
            trs.append(tr)
        if len(trs) < period:
            return None
        return float(np.mean(trs[-period:]))

    def _vol(self, closes: list[float], period: int) -> float | None:
        if len(closes) < period + 1:
            return None
        arr = np.array(closes[-(period + 1):])
        log_returns = np.log(arr[1:] / arr[:-1])
        return float(np.std(log_returns) * np.sqrt(252))

    def compute_trend(
        self,
        sma20: float | None,
        sma50: float | None,
        sma200: float | None,
        latest: float,
    ) -> str:
        if sma20 and sma50 and latest > sma20 and sma20 > sma50:
            return "uptrend"
        if sma200 and sma50 and sma20 and sma20 > sma50 and sma50 > sma200:
            return "uptrend"
        if sma20 and sma50 and latest < sma20 and sma20 < sma50:
            return "downtrend"
        return "sideways"

    def compute_momentum_score(
        self,
        rsi: float | None,
        macd: float | None,
        macd_signal: float | None,
        trend: str,
    ) -> float:
        score = 0.0
        if rsi is not None:
            if rsi > 70:
                score += 0.5
            elif rsi < 30:
                score -= 0.5
            else:
                score += (rsi - 50) / 100.0
        if macd is not None and macd_signal is not None:
            score += 0.3 if macd > macd_signal else -0.3
        if trend == "uptrend":
            score += 0.2
        elif trend == "downtrend":
            score -= 0.2
        return max(-1.0, min(1.0, score))
