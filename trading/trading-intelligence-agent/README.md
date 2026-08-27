# Trading Intelligence Agent

> This platform provides research and decision-support only. It does not provide personalized financial advice, tax advice, legal advice, or guaranteed investment outcomes. All decisions require human review.

Production-minded cross-asset decision-support backend for ETFs, equities, bonds, metals, and crypto.

## What Is Implemented

- Backend-owned SQL database foundation
- Seeded cross-asset universe and synthetic demo history
- Live provider paths for market, macro, filings, news, social, and crypto data
- Portfolio profile, position, policy-rule, and risk evaluation
- FastAPI routes and built-in operator dashboard
- Four-agent OpenAI Agents SDK investment-research workflow
- Deterministic offline committee demo and live model-backed execution path

## Four-Agent Research Workflow

```text
Research request + evidence bundle
        ├── Theme Scout
        ├── Evidence Analyst
        └── Risk & Valuation Analyst
                    ↓
        Investment Committee Manager
                    ↓
        Structured research dossier
```

The three specialists run concurrently. The committee manager reconciles their structured reports conservatively and returns one of:

- `advance_to_deeper_research`
- `watchlist_needs_trigger`
- `valuation_gated`
- `exposure_not_proven`
- `portfolio_overlap_concern`
- `risk_exceeds_reward`
- `reject`

Full installation and demo guide: [docs/investment-agents.md](./docs/investment-agents.md)

## Stack

- Python 3.12+
- OpenAI Agents SDK
- FastAPI
- Pydantic v2
- SQLAlchemy async ORM
- Alembic
- SQLite for local demo/tests
- PostgreSQL for Dockerized development/deployment

## Quick Start

```bash
cd trading-intelligence-agent
python -m venv .venv
source .venv/bin/activate       # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
cp .env.example .env            # Windows PowerShell: Copy-Item .env.example .env
```

### Offline four-agent demo

No API key required:

```bash
make run-committee-demo
```

### Live four-agent demo

Set these values in `.env`:

```dotenv
DEMO_MODE=false
OPENAI_API_KEY=your_key_here
OPENAI_AGENTS_MODEL=gpt-5.4-mini
```

Then run:

```bash
make run-committee-live
```

### API

```bash
make run-demo
```

Open `http://localhost:8000/` for the dashboard or `http://localhost:8000/docs` for API documentation.

The committee endpoint is:

```text
POST /research/committee
POST /research/committee?offline_demo=true
```

### Existing ingestion workflows

```bash
python -m scripts.bootstrap_live_data
python -m scripts.run_daily_job
python -m scripts.run_daily_research
```

## Core Commands

```bash
make setup
make run-demo
make run-committee-demo
make run-committee-live
make bootstrap-live
make run-daily-job
make run-daily-research
make test-unit
make test
make lint
make docker-up
```

## Key Routes

- `GET /health`
- `GET /`
- `GET /assets`
- `GET /assets/{symbol}`
- `GET /signals`
- `POST /signals/run`
- `GET /risk/{symbol}`
- `POST /research/committee`
- `POST /research/asset/{symbol}`
- `POST /research/daily-briefing`
- `GET /api/portfolio/profile`
- `GET /api/portfolio/policy`
- `POST /api/portfolio/evaluate`
- `GET /admin/providers`
- `POST /admin/jobs/bootstrap-live`
- `POST /admin/jobs/run-daily`
- `POST /admin/jobs/run-research`

## Database Notes

- Default local database: `sqlite+aiosqlite:///./data/trading_intel.db`
- Docker compose path: PostgreSQL 16 with `asyncpg`
- Alembic migrations live under `packages/storage/migrations/`

## Deployment

- Local Docker and cloud steps: [docs/deployment.md](./docs/deployment.md)
- Render blueprint: repo-root `render.yaml`
- Public deployments should set `ADMIN_API_TOKEN` and protect `/admin/*`
- Trace payload capture is disabled in `.env.example`; review tracing policy before production use

## Current Scope Limits

- No broker execution
- No autonomous trading
- The committee endpoint currently accepts an explicit evidence bundle
- Live provider credentials are required for current external data
- Full point-in-time walk-forward evaluation remains future work
- Committee dossier persistence and collaborative human review are not yet implemented

## Next Build Steps

1. Assemble committee evidence automatically from existing repositories and data providers.
2. Persist dossier revisions and human decisions.
3. Add ETF holdings look-through and portfolio overlap by underlying issuer.
4. Add point-in-time evaluation and research-outcome tracking.
5. Surface committee dossiers in the operator dashboard.
