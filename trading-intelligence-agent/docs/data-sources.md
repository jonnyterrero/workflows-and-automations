# Data Sources

## Supported Source Types

| Category | Demo Provider | Live Provider Options | API Key |
|----------|------------|----------------------|---------|
| Equities OHLCV | DemoMarketDataProvider (synthetic) | Polygon.io, Alpha Vantage, Alpaca | Yes |
| ETF OHLCV | DemoMarketDataProvider | Same as equities | Yes |
| Crypto OHLCV | DemoCryptoProvider (synthetic) | Binance, Coinbase | Optional |
| Macro Indicators | DemoMacroProvider (fixture) | FRED API, US Treasury | FRED: Yes, Treasury: No |
| News Articles | DemoNewsProvider (fixture) | NewsAPI, RSS feeds, IPO Scoop public calendar | Yes |
| Social Posts | DemoSocialProvider (fixture) | Reddit API, X/Twitter | Yes |
| SEC Filings | EDGARFilingsProvider (demo/live) | SEC EDGAR (free) | No (User-Agent header required) |
| Order Books | DemoCryptoProvider | Binance WebSocket | Optional |

## Rate Limits

| Provider | Limit | Notes |
|----------|-------|-------|
| Demo | Unlimited | Synthetic data |
| Polygon (free) | 5 req/min | Limited data |
| Alpha Vantage (free) | 5 req/min, 500/day | Good free tier |
| Alpaca (paper) | 200 req/min | Paper trading free |
| FRED | 120 req/min | Free with API key |
| SEC EDGAR | 10 req/sec | Free, User-Agent required |
| NewsAPI (free) | 100 req/day | Limited to dev use |
| Reddit (OAuth) | 60 req/min | Free API |
| Binance | 1200 req/min (signed) | Free read-only |

## Legal / Terms of Service Notes

- **SEC EDGAR**: Public data, free to use. Include User-Agent with contact email per EDGAR policy.
- **Reddit**: OK for research via official API. Do not scrape auth-gated content.
- **News sources**: RSS feeds are generally public. NewsAPI requires API key and has ToS for commercial use.
- **IPO Scoop**: Public calendar page currently allows basic access in `robots.txt`; use conservatively and avoid aggressive crawl patterns.
- **MarketWatch**: Do not HTML-scrape the site. Use the public RSS feeds only.
- **TheStreet**: Direct scraping is currently blocked by anti-bot controls; use licensed/API aggregators instead of bypass attempts.
- **Crypto exchanges**: Binance/Coinbase provide free public market data endpoints.
- **Do not scrape**: Do not bypass robots.txt, login pages, or anti-bot systems.
- **Do not redistribute**: Do not republish raw data in violation of provider ToS.

## Demo Mode

When `DEMO_MODE=true`, all providers return synthetic or fixture data:
- Market prices: seeded random walk based on symbol hash
- News: ~7 realistic fixture articles covering SPY, NVDA, AAPL, TSLA, ETH, BTC
- Social: ~10 fixture Reddit posts across investing/WSB/stocks/crypto
- Macro: 12 months of fixture indicator series
- Crypto: seeded synthetic OHLCV with realistic volatility

Demo mode requires **zero API keys** and works fully offline.
