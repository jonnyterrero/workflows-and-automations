# Deployment

## Local Docker

1. Copy `.env.example` to `.env`.
2. Set `DEMO_MODE=false`.
3. Add your provider keys and `ADMIN_API_TOKEN`.
4. Start the stack:

```bash
docker compose up -d postgres api worker collector
```

5. Bootstrap the live database once:

```bash
docker compose run --rm api python -m scripts.bootstrap_live_data
```

6. Run the full daily ingestion once:

```bash
docker compose run --rm api python -m scripts.run_daily_job
```

7. Open:
   - `http://localhost:8000/`
   - `http://localhost:8000/docs`
   - `http://localhost:8000/health`

## Render Cloud

The repo root contains `render.yaml` for a minimal cloud deployment:

- `trading-intelligence-api`: public FastAPI service
- `trading-intelligence-daily`: daily cron that runs the full ingestion job
- `trading-intelligence-research`: daily cron that generates watchlist signals and the briefing
- `trading-intel-db`: managed Postgres

### Steps

1. Push the repo to GitHub.
2. In Render, create a new Blueprint from the repository root.
3. Review `render.yaml`.
4. Fill the unsynced secrets:
   - `ADMIN_API_TOKEN`
   - `EDGAR_USER_AGENT`
   - `POLYGON_API_KEY`
   - `ALPHA_VANTAGE_API_KEY`
   - `FINNHUB_API_KEY`
   - `SEC_API_KEY`
   - `FRED_API_KEY`
   - `NEWSAPI_KEY`
   - `X_BEARER_TOKEN`
   - `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`
5. Deploy the Blueprint.
6. Optional: if you want data immediately instead of waiting for the next cron window, open a Render shell for the API service and run:

```bash
python -m scripts.run_daily_job
python -m scripts.run_daily_research
```

### Notes

- Set `ADMIN_API_TOKEN` to a value you control. Use it as `X-Admin-Token` or `Authorization: Bearer ...` for `/admin/*` routes.
- `initialDeployHook` on the API service runs `python -m scripts.bootstrap_live_data` once on first successful deploy.
- The cron schedule in `render.yaml` is UTC.
- The public deployment now includes a built-in operator dashboard at `/`.
- The raw API remains available at `/docs`.

## First Use

After deployment, use this sequence:

1. Open `/` and paste `ADMIN_API_TOKEN` into the dashboard.
2. If the watchlist is empty, `POST /admin/jobs/bootstrap-live`
3. `GET /health`
4. `GET /admin/providers`
5. `POST /admin/jobs/run-daily`
6. `POST /admin/jobs/run-research`
7. `GET /admin/corporate/NVDA`
8. `GET /admin/ipo-calendar`
9. `GET /research/daily-briefing/latest`

Example signal request:

```json
{
  "symbol": "NVDA",
  "horizon": "swing"
}
```
