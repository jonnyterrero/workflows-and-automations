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

**Migration fails**: Run `make reset-db` to drop and recreate the database.
