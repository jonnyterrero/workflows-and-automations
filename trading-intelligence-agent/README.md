# Trading Intelligence Agent

> This platform provides research and decision-support only. It does not provide personalized financial advice, tax advice, legal advice, or guaranteed investment outcomes. All decisions require human review.

Production-minded cross-asset decision-support backend for ETFs, equities, bonds, metals, and crypto. The current build focuses on the Phase 1 foundation from the master build prompt:

- backend-owned SQL database foundation
- seeded cross-asset universe
- pure portfolio policy and risk evaluation engine
- FastAPI routes for assets, signals, research, and portfolio evaluation
- local Docker/PostgreSQL path plus SQLite demo path
- deployment blueprint for Render plus live bootstrap tooling

## Stack

- FastAPI
- SQLAlchemy async ORM
- Alembic migrations
- SQLite for local demo and tests
- PostgreSQL for Dockerized development / deployment

## What Is Implemented

- Asset universe and watchlist seeding from the PDF-defined symbol list
- Synthetic OHLCV demo history for seeded assets
- Macro/news/social demo fixtures
- Live provider path for Polygon, Alpha Vantage, Coinbase Exchange, Finnhub, NewsAPI, RSS, IPO Scoop, SEC-API, EDGAR, Reddit, and X
- Portfolio profile, position, and policy-rule persistence
- Pure `evaluate_portfolio_decision(...)` policy engine with unit coverage
- API route for `/api/portfolio/evaluate`
- Corporate intelligence ingestion for fundamentals, earnings/IPO calendar, and recent filings

## Quick Start

### Live Mode

```bash
cd trading-intelligence-agent
cp .env.example .env
python -m pip install -e ".[dev]"
python -m scripts.bootstrap_live_data
python -m uvicorn apps.api_service.main:app --reload --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000/` for the operator dashboard or `http://localhost:8000/docs` for raw API docs.

Run the full ingestion cycle:

```bash
python -m scripts.run_daily_job
python -m scripts.run_daily_research
```

### Demo Mode

```bash
python -m scripts.seed_demo_data
python -m uvicorn apps.api_service.main:app --reload --host 0.0.0.0 --port 8000
```

## Core Commands

```bash
make setup
make bootstrap-live
make run-daily-job
make run-daily-research
make run-demo
make test
make docker-up
```

## Key Routes

- `GET /health`
- `GET /`
- `GET /assets`
- `GET /assets/{symbol}`
- `GET /admin/providers`
- `GET /admin/corporate/{symbol}`
- `GET /admin/ipo-calendar`
- `POST /admin/jobs/run-daily`
- `POST /admin/jobs/run-research`
- `GET /signals`
- `POST /signals/run`
- `GET /risk/{symbol}`
- `GET /api/portfolio/profile`
- `GET /api/portfolio/policy`
- `POST /api/portfolio/evaluate`

## Database Notes

- Default local database: `sqlite+aiosqlite:///./data/trading_intel.db`
- Docker compose path: PostgreSQL 16 with `asyncpg`
- Alembic migration added: `002_portfolio_policy_foundation.py`

## Deployment

- Local Docker and cloud steps: [docs/deployment.md](./docs/deployment.md)
- Render blueprint: repo-root `render.yaml`
- Public deployments should set `ADMIN_API_TOKEN` and send it on `/admin/*` calls

## Current Scope Limits

- No broker execution
- No autonomous trading
- Built-in operator dashboard at `/`
- Data adapters remain key-driven unless real provider credentials are added
- Backtesting tables exist, but full walk-forward evaluation is not yet the primary path

## Suggested Next Build Steps

1. Resolve X API auth and verify social ingestion live.
2. Add decision-output persistence and human review endpoints.
3. Build a dashboard client against the FastAPI routes.
4. Improve provider-specific retries, quotas, and admin observability.
