# Runbook

## Current state

- Phase: 0 — infrastructure bootstrap
- Trading mode: disabled
- Ingestion mode: no-op stub
- Pilot: not yet confirmed; Phase 1 is blocked until the owner selects a
  politician- or 13F-based pilot
- Options: no options execution
- Planned approval UI: a small Vercel application in a later phase

## Local checks

```bash
uv sync --locked
uv run ruff check .
uv run python ingest/normalize.py
uv run python validate/autopilot_diff.py
```

The Phase 0 commands perform no network, database, brokerage, or exchange
operations.

## Secrets

Create `.env` locally from `.env.example`. Never commit it. Store scheduled-job
credentials in GitHub Secrets. The Supabase service-role key is server-side
only. OKX credentials must be trade-scoped, withdrawal-disabled, and validated
against the demo profile before any live profile is created.

Vanguard and Fidelity credentials are permanently out of scope.

## Execution incident rule

If approval state, portfolio state, or preflight results are ambiguous, abort
the entire batch. Do not partially execute, retry automatically, or infer
approval.

## Planned OKX DCA policy

No automation may touch the DCA plan before demo validation and explicit owner
approval. The existing monthly allocation is $100–200 total:

- BTC 40%
- ETH 30%
- SOL 10%
- UNI 10%
- ADA 10%
