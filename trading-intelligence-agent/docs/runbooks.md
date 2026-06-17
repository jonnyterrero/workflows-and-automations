# Runbooks

## Starting the API (Local)

```bash
# First time
make setup

# Start API server
make run-api

# Demo mode (no API keys)
make run-demo

# Check health
make health
```

## Running the Scheduler

```bash
# Runs daily collection on cron + immediately on startup
make run-scheduler
```

## Seeding Demo Data

```bash
make seed
# or
python -m scripts.seed_demo_data
```

## Running Tests

```bash
make test

# Unit tests only
make test-unit

# Integration tests only
make test-integration
```

## Running a Full Daily Collection via API

```bash
curl -X POST http://localhost:8000/admin/jobs/run-daily
```

The daily job now includes:

- market prices/quotes
- macro indicators + yield curve
- crypto prices/tickers/order books
- news + social ingestion
- corporate fundamentals, earnings/IPO calendar, and SEC filings snapshots

## Generating a Signal

```bash
curl -X POST http://localhost:8000/signals/run \
  -H "Content-Type: application/json" \
  -d '{"symbol": "NVDA", "horizon": "swing"}'
```

## Generating a Daily Briefing

```bash
curl -X POST http://localhost:8000/research/daily-briefing
```

## Resetting the Database

```bash
make reset-db
```

## Docker Setup

```bash
# Copy env file
cp .env.example .env

# Build and start all services
docker-compose up -d

# Watch logs
docker-compose logs -f api

# Stop everything
docker-compose down -v
```

## Troubleshooting

**ImportError on startup**: Ensure `PYTHONPATH=.` or run via `make run-api`.

**Database locked**: Kill any other processes with the SQLite file open.

**No prices for symbol**: Run `POST /admin/jobs/run-ingestion` or `make seed` first.

**LLM returns demo response**: Set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` in `.env` and `DEMO_MODE=false`.

**X/Twitter ingestion empty (known blocker)**: Bearer token must be copied from developer.x.com → App → Keys and tokens → **Bearer Token** (not API Key). Paste raw token into `.env` (`+` and `=` are OK; avoid URL-encoded `%2B`/`%3D` from browser links). Verify with `GET /admin/setup/x` and `POST /admin/setup/x/verify`. If 401 persists, regenerate the bearer token in the portal. Reddit + crypto RSS still work without X.

**Inspect corporate catalysts**: Use `GET /admin/corporate/{symbol}` for the latest stored fundamentals/catalyst snapshot and recent filings. Use `GET /admin/ipo-calendar` to inspect the latest Finnhub IPO calendar response when `FINNHUB_API_KEY` is configured.

**Broader market context**: `POST /admin/jobs/run-daily` now stores both symbol-targeted news and a general-market sweep. That general pass is what picks up broad RSS headlines, Finnhub general news, NewsAPI broad queries, and IPO Scoop calendar items.

**Migration fails**: Run `make reset-db` to drop and recreate the database.
