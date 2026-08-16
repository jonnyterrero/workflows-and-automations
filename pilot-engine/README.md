# Pilot Engine

Self-hosted, recommend-only copy-trading pipeline for public STOCK Act and 13F
disclosures. The engine computes deterministic target weights and proposed
orders for an experimental brokerage sleeve. It never executes an order without
fresh human approval.

## Architecture

```mermaid
flowchart TD
    A["INGEST (GitHub Actions daily cron, no AI)<br/>Capitol Trades scraper / SEC EDGAR 13F parser<br/>Firebase Admin SDK writes"]
    B["FIRESTORE — system of record<br/>Spark tier, server-only<br/>pilot_trades → pilot_holdings → target_weights"]
    C["SIGNAL (deterministic Python — never an LLM)<br/>diff target weights vs current Public holdings<br/>→ proposed order batch<br/>(fractional sizing, min-order filters)"]
    D["CLAUDE (analysis + presentation only)<br/>reads Firestore + Public/OKX MCP state<br/>summarizes batch + rationale"]
    E{"HUMAN APPROVES"}
    F["EXECUTION (workflow_dispatch)<br/>requires current batch status == approved<br/>Public: preflight_order → place_order<br/>OKX: demo profile first"]

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
- Keep Firebase service-account JSON and every API key out of Git.
- OKX begins on a trade-only demo profile with withdrawals disabled.
- Vanguard and Fidelity credentials are never used by this project.

## Phase 0

Phase 0 provides deny-all Firestore rules, declared indexes, typed Admin SDK
helpers, Python 3.12/`uv` tooling, Ruff and pytest checks, no-op scheduled
workflows, and a dispatch-only approval gate. Brokerage execution remains
intentionally unimplemented.

```bash
uv sync --locked
uv run ruff check .
npx -y firebase-tools@latest emulators:exec \
  --only firestore \
  --project demo-pilot-engine \
  --config firebase/firebase.json \
  "uv run pytest"
```

Copy `.env.example` to `.env` only in a trusted local environment. Never commit
the resulting file or service-account JSON. Store the service-account JSON in
the `FIREBASE_SERVICE_ACCOUNT_JSON` GitHub Secret.

See `docs/runbook.md` for emulator, deployment, and source-seeding commands.
