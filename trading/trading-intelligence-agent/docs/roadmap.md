# Product Roadmap

## Phase 1 (Current MVP) — Local Research Agent
- ✅ Scaffold repo and data models
- ✅ SQLite database with Alembic migrations
- ✅ FastAPI service with all core endpoints
- ✅ Demo mode (no paid API keys required)
- ✅ Demo market data, news, social, macro providers
- ✅ Ticker extraction (regex + lexicon)
- ✅ Sentiment scoring (lexicon-based)
- ✅ Technical analysis (pure Python/NumPy)
- ✅ Signal engine with configurable weights
- ✅ Risk flag engine
- ✅ AI research agent (OpenAI/Anthropic adapter)
- ✅ Daily briefing generation
- ✅ Asset research report generation
- ✅ Backtesting replay foundation
- ✅ Docker compose setup

## Phase 2 — Stronger Data Providers
- [x] Polygon.io market data adapter
- [x] Alpha Vantage adapter (equities + crypto OHLCV)
- [x] FRED API macro adapter (real FRED data)
- [x] NewsAPI.org adapter (free dev tier, budget-limited)
- [x] Finnhub news + fundamentals + earnings/IPO calendar adapters
- [x] Reddit API adapter (public JSON search)
- [x] RSS news (Reuters, Bloomberg Markets, Yahoo)
- [x] Crypto RSS catalog (`config/crypto_rss_feeds.yaml` — 15 feeds, reliability-weighted)
- [x] SEC EDGAR live submissions API (CIK lookup)
- [ ] X/Twitter API v2 social ingestion — **blocked: bearer token returns 401; regenerate at developer.x.com, verify via `POST /admin/setup/x/verify`**
- [x] Coinbase Exchange public market-data adapter
- [ ] DeFiLlama public API (TVL/yields — free, next up)
- [ ] CoinGlass / Glassnode / Nansen (API keys required)
- [x] Fundamental data (Finnhub basic financials + earnings calendar)

## Phase 3 — Dashboard UI
- [ ] Next.js dashboard
- [ ] Watchlist management UI
- [ ] Signal explorer with evidence viewer
- [ ] Daily briefing reader
- [ ] Risk panel
- [ ] Asset candle chart with TA overlays

## Phase 4 — Backtesting & Validation
- [ ] Full signal backtest with configurable lookforward windows
- [ ] Walk-forward validation
- [ ] Signal decay analysis
- [ ] Sharpe / Calmar / max drawdown reporting
- [ ] Comparison against buy-and-hold baseline

## Phase 5 — Paper Trading
- [ ] Paper trading journal (log hypothetical entries/exits)
- [ ] P&L simulation from signal-triggered entries
- [ ] No real money, no broker connection
- [ ] Performance reporting

## Phase 6 — Broker Integration (Post Risk Controls)
- [ ] Alpaca paper trading first
- [ ] Hard position sizing limits
- [ ] Kill switch / circuit breaker
- [ ] Drawdown limit enforcement
- [ ] Audit log of all order attempts
- [ ] Only after Phase 4 shows acceptable win rate
- [ ] **Never automated — human approval required per order**

## Phase 7 — Production Deployment
- [ ] PostgreSQL + TimescaleDB for time-series
- [ ] Redis for task queuing
- [ ] Kubernetes deployment
- [ ] Prometheus + Grafana metrics
- [ ] PagerDuty alerting
- [ ] Multi-user support with auth

## Non-Goals (Explicit Out of Scope)
- Fully autonomous trading without human oversight
- Guaranteed return predictions
- Broker credential storage without HSM
- Scraping private/gated content
- Market manipulation signals
