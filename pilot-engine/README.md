# Pilot Engine

Self-hosted, recommend-only copy-trading pipeline for public STOCK Act and 13F
disclosures. The engine computes deterministic target weights and proposed
orders for an experimental brokerage sleeve. It never executes an order without
fresh human approval.

## Architecture

```mermaid
flowchart TD
    A["INGEST (scheduled, no AI)<br/>Capitol Trades scraper / SEC EDGAR 13F parser<br/>daily cron via GitHub Actions or Supabase Edge Function"]
    B["SUPABASE — system of record<br/>pilot_trades → pilot_holdings → target_weights"]
    C["SIGNAL (deterministic Python — never an LLM)<br/>diff target weights vs current Public holdings<br/>→ proposed order batch<br/>(fractional sizing, min-order filters)"]
    D["CLAUDE (analysis + presentation only)<br/>reads Supabase + Public/OKX MCP state<br/>drafts order batch + rationale"]
    E{"HUMAN APPROVES"}
    F["EXECUTION<br/>Public: preflight_order → place_order<br/>OKX: official Agent Trade Kit MCP<br/>(demo profile first)"]

    A --> B --> C --> D --> E
    E -->|approved only| F
```

Deterministic code makes every trading and sizing decision. An LLM may explain
or present a proposed batch, but it does not compute positions or authorize
execution.

## Non-negotiable guardrails

- Recommend-only by default; execution requires explicit, fresh human approval.
- Experimental sleeve: at most 5% of investable assets, with reassessment at
  10%.
- Single-name target: at most 3%; hard maximum: 5%.
- Stop contributions unless the sleeve beats VTI after all costs over 12–18
  months.
- Keep all credentials out of Git. OKX begins on a trade-only demo profile with
  withdrawals disabled.
- Vanguard and Fidelity credentials are never used by this project.

## Phase 0

Phase 0 provides the database migration, Python 3.12/`uv` tooling, Ruff linting,
and no-op scheduled workflows. Data ingestion, signal generation, and execution
remain intentionally unimplemented.

```bash
uv sync --locked
uv run ruff check .
uv run python ingest/normalize.py
```

Copy `.env.example` to `.env` only in a trusted local environment. Never commit
the resulting file. Store automation credentials in GitHub Secrets.
