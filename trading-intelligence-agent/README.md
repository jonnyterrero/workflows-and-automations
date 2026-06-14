# Trading Intelligence Agent

> This platform provides research and decision-support only. It does not provide personalized financial advice, tax advice, legal advice, or guaranteed investment outcomes. All decisions require human review.

Production-minded cross-asset decision-support backend for ETFs, equities, bonds, metals, and crypto. The current build focuses on the Phase 1 foundation from the master build prompt:

- backend-owned SQL database foundation
- seeded cross-asset universe
- pure portfolio policy and risk evaluation engine
- FastAPI routes for assets, signals, research, and portfolio evaluation
- local Docker/PostgreSQL path plus SQLite demo path

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
- Portfolio profile, position, and policy-rule persistence
- Pure `evaluate_portfolio_decision(...)` policy engine with unit coverage
- API route for `/api/portfolio/evaluate`

## Quick Start

```bash
cd trading-intelligence-agent
cp .env.example .env
python -m pip install -e ".[dev]"
python -m scripts.seed_demo_data
uvicorn apps.api_service.main:app --reload --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000/docs`.

## Core Commands

```bash
make setup
make run-demo
make test
make docker-up
```

## Key Routes

- `GET /health`
- `GET /assets`
- `GET /assets/{symbol}`
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

## Current Scope Limits

- No broker execution
- No autonomous trading
- No dashboard frontend yet
- Data adapters remain demo/seed-first unless real provider credentials are added
- Backtesting tables exist, but full walk-forward evaluation is not yet the primary path

## Suggested Next Build Steps

1. Replace seeded/demo data with real yfinance, CoinGecko, and FRED adapters.
2. Add decision-output persistence and human review endpoints.
3. Build a dashboard client against the FastAPI routes.
4. Add walk-forward backtest orchestration and result visualizations.
