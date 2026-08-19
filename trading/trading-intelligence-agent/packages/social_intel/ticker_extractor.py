"""Ticker extraction and disambiguation from financial text."""
from __future__ import annotations

import re

KNOWN_TICKERS: frozenset[str] = frozenset({
    "SPY", "QQQ", "TLT", "IWM", "GLD", "SLV", "USO", "VXX", "UVXY",
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "META", "NVDA", "TSLA",
    "AMD", "INTC", "QCOM", "MU", "NFLX", "ORCL", "CRM", "ADBE", "AVGO",
    "JPM", "BAC", "WFC", "GS", "MS", "C", "USB", "BRK", "BX",
    "JNJ", "PFE", "MRK", "ABBV", "UNH", "CVS", "LLY", "AMGN", "GILD",
    "WMT", "COST", "TGT", "AMZN", "HD", "LOW",
    "XOM", "CVX", "COP", "SLB", "OXY",
    "V", "MA", "PYPL", "SQ", "COIN", "HOOD",
    "UBER", "LYFT", "ABNB", "DASH", "SNAP", "PINS", "SPOT",
    "PLTR", "RBLX", "DKNG", "GME", "AMC", "BB", "NOK",
    "RIVN", "LCID", "F", "GM", "TM", "STLA",
    "DIS", "NFLX", "WBD", "PARA", "FOX",
    "T", "VZ", "TMUS",
    "BA", "LMT", "NOC", "RTX", "GD",
    "CAT", "DE", "HON", "MMM", "GE", "ETN",
})

CRYPTO_TICKERS: frozenset[str] = frozenset({
    "BTC", "ETH", "SOL", "BNB", "ADA", "DOGE", "XRP", "DOT",
    "AVAX", "MATIC", "LINK", "UNI", "AAVE", "SHIB", "LTC",
})

AMBIGUOUS_WORDS: frozenset[str] = frozenset({
    "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L",
    "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X",
    "Y", "Z", "AI", "GO", "DO", "IT", "IS", "BE", "OR", "IF", "OF",
    "AT", "IN", "ON", "UP", "MY", "BY", "PM", "AM", "DD", "PE", "EV",
    "IP", "VR", "AR", "ML", "DL", "IT", "UI", "UX", "CD", "SD", "HD",
    "OK", "NO", "US", "UK", "EU", "CA", "NY", "LA", "DC", "RE", "CO",
    "EPS", "IPO", "ETF", "API", "APR", "APY", "CEO", "CFO", "CTO",
    "ATH", "ATL", "FUD", "FOMO", "YOLO", "RIP", "IMO", "TBH",
})

_DOLLAR_TICKER = re.compile(r"\$([A-Z]{1,6}(?:\.[A-Z]{1,2})?)")
_BARE_CAPS = re.compile(r"\b([A-Z]{2,6})\b")
_CRYPTO_CONTEXT = re.compile(
    r"(?:buying|sold|long|short|holding|bought|sell|invest|bullish on|bearish on|dump|pump)\s+([A-Z]{2,6})",
    re.IGNORECASE,
)

_CRYPTO_USD_MAP: dict[str, str] = {
    "BTC": "BTC-USD", "ETH": "ETH-USD", "SOL": "SOL-USD",
    "BNB": "BNB-USD", "ADA": "ADA-USD", "DOGE": "DOGE-USD",
    "XRP": "XRP-USD", "DOT": "DOT-USD", "AVAX": "AVAX-USD",
    "MATIC": "MATIC-USD", "LINK": "LINK-USD", "UNI": "UNI-USD",
    "SHIB": "SHIB-USD", "LTC": "LTC-USD",
}


def _normalize(raw: str) -> str:
    raw = raw.strip().lstrip("$").rstrip(".,;!?")
    if raw.upper() in _CRYPTO_USD_MAP:
        return _CRYPTO_USD_MAP[raw.upper()]
    return raw.upper()


class TickerExtractor:
    def extract(self, text: str) -> list[str]:
        found: set[str] = set()

        # 1. $TICKER — highest confidence
        for m in _DOLLAR_TICKER.findall(text):
            sym = _normalize(m)
            if sym not in AMBIGUOUS_WORDS:
                found.add(sym)

        # 2. Bare ALL-CAPS words that are in KNOWN_TICKERS
        for m in _BARE_CAPS.findall(text):
            sym = m.upper()
            if sym in KNOWN_TICKERS and sym not in AMBIGUOUS_WORDS:
                found.add(sym)

        # 3. Crypto in action-verb context
        for m in _CRYPTO_CONTEXT.findall(text):
            sym = m.upper()
            if sym in CRYPTO_TICKERS:
                found.add(_CRYPTO_USD_MAP.get(sym, sym))

        return sorted(found)

    def extract_with_context(self, text: str) -> list[dict]:
        results: list[dict] = []
        seen: set[str] = set()

        for m in _DOLLAR_TICKER.findall(text):
            sym = _normalize(m)
            if sym not in AMBIGUOUS_WORDS and sym not in seen:
                seen.add(sym)
                asset_type = "crypto" if "-USD" in sym else ("etf" if sym in {"SPY","QQQ","TLT","IWM","GLD"} else "equity")
                results.append({"ticker": sym, "context": "$-prefix", "confidence": 1.0, "asset_type": asset_type})

        for m in _BARE_CAPS.findall(text):
            sym = m.upper()
            if sym in KNOWN_TICKERS and sym not in AMBIGUOUS_WORDS and sym not in seen:
                seen.add(sym)
                asset_type = "etf" if sym in {"SPY","QQQ","TLT","IWM"} else "equity"
                results.append({"ticker": sym, "context": "known-ticker", "confidence": 0.8, "asset_type": asset_type})

        for m in _CRYPTO_CONTEXT.findall(text):
            sym = m.upper()
            if sym in CRYPTO_TICKERS:
                full = _CRYPTO_USD_MAP.get(sym, sym)
                if full not in seen:
                    seen.add(full)
                    results.append({"ticker": full, "context": "crypto-verb-context", "confidence": 0.5, "asset_type": "crypto"})

        return results

    def normalize_symbol(self, raw: str) -> str:
        return _normalize(raw)
