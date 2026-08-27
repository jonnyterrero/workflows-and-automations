"""Market data tools for the Trading agent.

These wrap free/freemium APIs so the starter works out of the box, but the
function bodies are easy to swap for paid feeds (Polygon, IEX, Bloomberg, etc.).
"""
from __future__ import annotations

import datetime as dt
from typing import Any

import httpx
from agents import function_tool

from ..common.config import settings
from ..common.logging import get_logger

log = get_logger(__name__)


@function_tool
def get_quote(symbol: str) -> dict[str, Any]:
    """Fetch a near-real-time equity quote.

    Args:
        symbol: Ticker symbol, e.g. "AAPL", "NVDA", "SPY".

    Returns:
        Dict with last price, day change, day range, volume, and a timestamp.
    """
    try:
        import yfinance as yf

        t = yf.Ticker(symbol)
        info = t.fast_info
        return {
            "symbol": symbol.upper(),
            "last_price": float(info.last_price),
            "previous_close": float(info.previous_close),
            "day_low": float(info.day_low),
            "day_high": float(info.day_high),
            "volume": int(info.last_volume or 0),
            "currency": info.currency,
            "as_of": dt.datetime.utcnow().isoformat() + "Z",
            "source": "yfinance",
        }
    except Exception as e:  # noqa: BLE001
        log.warning("get_quote failed for %s: %s", symbol, e)
        return {"symbol": symbol, "error": str(e)}


@function_tool
def get_price_history(symbol: str, period: str = "3mo", interval: str = "1d") -> dict[str, Any]:
    """Return OHLCV history for charting / momentum analysis.

    Args:
        symbol: Ticker symbol.
        period: yfinance period string (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max).
        interval: 1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo.
    """
    import yfinance as yf

    df = yf.Ticker(symbol).history(period=period, interval=interval, auto_adjust=False)
    if df.empty:
        return {"symbol": symbol, "error": "no data"}
    df = df.tail(120)  # cap payload
    rows = [
        {
            "t": idx.isoformat(),
            "o": float(r.Open),
            "h": float(r.High),
            "l": float(r.Low),
            "c": float(r.Close),
            "v": int(r.Volume),
        }
        for idx, r in df.iterrows()
    ]
    closes = [r["c"] for r in rows]
    return {
        "symbol": symbol.upper(),
        "interval": interval,
        "period": period,
        "rows": rows,
        "summary": {
            "first_close": closes[0],
            "last_close": closes[-1],
            "pct_change": round((closes[-1] / closes[0] - 1) * 100, 2),
            "min": min(closes),
            "max": max(closes),
        },
    }


@function_tool
def get_fundamentals(symbol: str) -> dict[str, Any]:
    """Return key fundamental ratios and the latest income-statement line items."""
    import yfinance as yf

    t = yf.Ticker(symbol)
    info = t.info or {}
    keys = [
        "longName", "sector", "industry", "marketCap", "trailingPE", "forwardPE",
        "priceToBook", "profitMargins", "returnOnEquity", "debtToEquity",
        "freeCashflow", "totalRevenue", "earningsGrowth", "revenueGrowth",
        "dividendYield", "beta", "fiftyTwoWeekHigh", "fiftyTwoWeekLow",
    ]
    return {"symbol": symbol.upper(), **{k: info.get(k) for k in keys}}


@function_tool
def get_market_news(symbol: str | None = None, limit: int = 8) -> list[dict[str, Any]]:
    """Recent news headlines for a symbol or the broader market."""
    import yfinance as yf

    if symbol:
        items = yf.Ticker(symbol).news or []
    else:
        # Fall back to SPY headlines as a market proxy.
        items = yf.Ticker("SPY").news or []
    out = []
    for n in items[:limit]:
        out.append(
            {
                "title": n.get("title"),
                "publisher": n.get("publisher"),
                "link": n.get("link"),
                "published": n.get("providerPublishTime"),
            }
        )
    return out


@function_tool
async def get_social_sentiment(symbol: str, limit: int = 25) -> dict[str, Any]:
    """Fetch recent Reddit/StockTwits chatter for a ticker and score sentiment.

    Uses the public Reddit search JSON endpoint (no auth) plus StockTwits.
    Returns counts and a naive bullish/bearish ratio derived from keyword scoring.
    """
    bullish = {"buy", "long", "moon", "calls", "bull", "rip", "🚀", "pump", "breakout"}
    bearish = {"sell", "short", "puts", "bear", "dump", "crash", "rug", "down", "drill"}

    posts: list[dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=15, headers={"User-Agent": "agent-trio/0.1"}) as c:
        # Reddit
        try:
            r = await c.get(
                "https://www.reddit.com/r/wallstreetbets+stocks+investing/search.json",
                params={"q": symbol, "restrict_sr": "true", "sort": "new", "limit": limit},
            )
            for child in r.json().get("data", {}).get("children", []):
                d = child["data"]
                posts.append({"src": "reddit", "title": d.get("title", ""), "score": d.get("score", 0)})
        except Exception as e:  # noqa: BLE001
            log.warning("reddit fetch failed: %s", e)

        # StockTwits
        try:
            r = await c.get(f"https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json")
            for m in r.json().get("messages", [])[:limit]:
                posts.append({"src": "stocktwits", "title": m.get("body", ""), "score": 1})
        except Exception as e:  # noqa: BLE001
            log.warning("stocktwits fetch failed: %s", e)

    bull = bear = 0
    for p in posts:
        text = p["title"].lower()
        if any(w in text for w in bullish):
            bull += 1
        if any(w in text for w in bearish):
            bear += 1
    total = max(bull + bear, 1)
    return {
        "symbol": symbol.upper(),
        "post_count": len(posts),
        "bullish_mentions": bull,
        "bearish_mentions": bear,
        "bull_bear_ratio": round(bull / total, 2),
        "sample": posts[:10],
    }


@function_tool
def position_sizing(account_equity: float, risk_pct: float, entry: float, stop: float) -> dict[str, Any]:
    """Fixed-fractional position sizing.

    Args:
        account_equity: Total liquid account value, USD.
        risk_pct: Percent of equity to risk on the trade (e.g. 0.5 for 0.5%).
        entry: Planned entry price.
        stop: Hard stop-loss price.
    """
    if entry <= 0 or stop <= 0 or entry == stop:
        return {"error": "invalid prices"}
    risk_per_share = abs(entry - stop)
    dollar_risk = account_equity * (risk_pct / 100.0)
    shares = int(dollar_risk // risk_per_share)
    return {
        "shares": shares,
        "dollar_risk": round(dollar_risk, 2),
        "risk_per_share": round(risk_per_share, 4),
        "notional": round(shares * entry, 2),
        "r_multiple_target_2R": round(entry + 2 * (entry - stop), 4),
    }
