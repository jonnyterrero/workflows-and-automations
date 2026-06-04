# Trading Intelligence Agent

> **DISCLAIMER: This is research and decision-support software, not financial advice.
> All signals carry uncertainty. Never make investment decisions based solely on this system.
> Past signal performance does not predict future returns.**

AI-powered trading research and decision-support platform for stocks, ETFs, bonds, and crypto.

## What It Does

- Collects market data, macro indicators, news, social posts, and SEC filings
- Extracts ticker mentions and scores sentiment from text
- Computes transparent, decomposable signal scores with configurable weights
- Flags risk conditions per asset class
- Generates AI-powered daily briefings and asset research reports (with LLM API key)
- Backtests historical signals against stored price data
- Exposes everything via a FastAPI REST API
- Runs fully in demo mode (no API keys required)

## What It Does NOT Do

- Execute trades or connect to brokers
- Give guaranteed buy/sell recommendations
- Store broker credentials
- Scrape private/authenticated content
- Claim guaranteed profitability

## Quick Start

```bash
# 1. Clone and enter project
cd trading-intelligence-agent

# 2. Copy environment file
cp .env.example .env

# 3. Install and set up (creates DB, runs migrations, seeds demo data)
make setup

# 4. Start the API server
make run-demo   # demo mode, no API keys needed
# OR
make run-api    # uses .env settings
```

Open http://localhost:8000/docs for interactive API docs.

## Environment Variables

See [`.env.example`](.env.example) for all variables. Key ones:

| Variable | Default | Description |
|----------|---------|-------------|
| `DEMO_MODE` | `true` | Use fixture data, no real API keys needed |
| `DATABASE_URL` | SQLite | Database connection string |
| `LLM_PROVIDER` | `openai` | `openai` or `anthropic` |
| `OPENAI_API_KEY` | (empty) | Enables real AI analysis |
| `ANTHROPIC_API_KEY` | (empty) | Alternative LLM provider |
| `DEFAULT_WATCHLIST` | `SPY,QQQ,...` | Default asset watchlist |

## Running Locally

```bash
make setup          # install deps + migrate + seed
make run-api        # start API on :8000
make run-worker     # start AI research worker
make run-scheduler  # start daily data collection scheduler
make run-demo       # all in demo mode (no API keys)
make test           # run all tests
make lint           # check code quality
```

## API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Service health check |
| GET | `/assets` | List all assets |
| GET | `/assets/watchlist` | Get watchlist |
| POST | `/assets/watchlist` | Add to watchlist |
| GET | `/market/{symbol}/prices` | Historical OHLCV |
| GET | `/market/{symbol}/candles` | Candles + technicals |
| GET | `/news` | Recent news |
| GET | `/news/{symbol}` | Symbol-filtered news + sentiment |
| GET | `/signals` | Recent signals |
| POST | `/signals/run` | Generate signal for symbol |
| GET | `/signals/{id}/evidence` | Signal evidence chain |
| POST | `/research/daily-briefing` | Generate AI daily briefing |
| GET | `/research/daily-briefing/latest` | Latest briefing |
| POST | `/research/asset/{symbol}` | Generate asset report |
| GET | `/risk/{symbol}` | Risk assessment |
| POST | `/backtest/signal-strategy` | Replay signals vs prices |
| POST | `/admin/jobs/run-daily` | Trigger full data collection |

Full API docs: http://localhost:8000/docs

## Demo Mode

Demo mode (`DEMO_MODE=true`) uses synthetic/fixture data:
- **Market prices**: Seeded random walk (deterministic by symbol)
- **News**: 7 fixture articles (NVDA, AAPL, TSLA, ETH, Fed, BTC)
- **Social**: 10 fixture Reddit posts (r/investing, r/WSB, r/crypto)
- **Macro**: 12 months fixture series (fed funds, CPI, yields, VIX, DXY)
- **Crypto**: Seeded synthetic OHLCV with realistic volatility

LLM analysis returns a placeholder message in demo mode. Set `OPENAI_API_KEY` + `DEMO_MODE=false` for real analysis.

## Docker

```bash
cp .env.example .env
docker-compose up -d
docker-compose logs -f api
```

## Testing

```bash
make test           # all tests
make test-unit      # unit tests only (fast, no DB)
make test-integration  # API tests
```

Tests use `DEMO_MODE=true` with an in-memory SQLite DB. No API keys required.

## Documentation

- [Architecture](docs/architecture.md)
- [Signal Methodology](docs/signal-methodology.md)
- [Risk Methodology](docs/risk-methodology.md)
- [Data Sources](docs/data-sources.md)
- [Runbooks](docs/runbooks.md)
- [Roadmap](docs/roadmap.md)

## Known Limitations

1. **Demo data only**: Default setup uses synthetic prices and fixture news/social
2. **Lexicon sentiment**: Sentiment analysis is keyword-based, not ML-based
3. **No fundamental data**: P/E, earnings, revenue not included in MVP without paid provider
4. **SQLite**: Not suitable for production time-series at scale; upgrade to PostgreSQL + TimescaleDB
5. **No real-time WebSocket**: Crypto WebSocket stream planned for Phase 2
6. **LLM hallucination risk**: AI reports cite only stored evidence IDs, but quality depends on data freshness
7. **No portfolio tracking**: No position sizing, correlation analysis, or portfolio-level risk

## Next Engineering Steps

1. Add Polygon.io or Alpha Vantage market data adapter (replace demo)
2. Add FRED API adapter for real macro data
3. Add Reddit API adapter (OAuth) for real social posts
4. Move from SQLite to PostgreSQL for production
5. Build Next.js dashboard (signal explorer, evidence viewer)
6. Add walk-forward backtesting validation
7. Add ML-based sentiment model (fine-tuned FinBERT or similar)
