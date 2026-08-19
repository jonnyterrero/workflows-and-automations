# Pilot Engine — Project Start / Handoff Doc

**Version:** 2 — Firebase backend
**Project:** DIY copy-trading engine replacing Autopilot subscription
**Owner:** Jonathan Terrero
**Created:** 2026-08-16
**Status:** Phase 0
**Working name:** `pilot-engine`

Version 2 supersedes the original Supabase design.

## 1. One-liner

Replace the Autopilot subscription with a self-hosted pipeline that ingests
public STOCK Act and 13F trade disclosures, computes target portfolio weights,
and generates order batches for the Public brokerage experimental sleeve, with
a human approval gate before execution.

## 2. Why this exists

- Politician portfolios come from STOCK Act disclosures and hedge-fund
  portfolios from 13F filings. Both are public.
- A pipeline consuming the same filings has the same structural disclosure lag.
- Removing the subscription lowers the sleeve's largest recurring cost.
- Creator portfolios based on private, real-time trading are not replicable.
  Confirm a politician- or 13F-based pilot before Phase 1.

## 3. Backend decision

Firestore is the system of record on Firebase Spark:

- No Cloud Functions, Cloud Scheduler, or Cloud Storage.
- Scheduled and compute work runs in GitHub Actions.
- Firestore is server-only. Firebase Admin SDK credentials are available only
  to trusted Actions jobs and local server scripts.
- Firestore Security Rules deny all client access.
- If Firestore becomes unsuitable, the fallback is a Postgres schema in an
  existing Supabase project. That fallback is not currently planned.

## 4. Hard guardrails

1. Recommend-only by default. Every live batch needs fresh human approval.
2. Experimental sleeve at most 5% of investable assets; reassess at 10%.
3. Single-name target at most 3%; hard maximum 5%.
4. Stop contributions unless the sleeve beats VTI after all costs over 12–18
   months.
5. Never commit secrets. Service-account JSON and API keys belong in GitHub
   Secrets; `.env` is local-only.
6. OKX begins on a trade-only demo profile with withdrawals disabled.
7. Agents never receive Vanguard or Fidelity credentials. Plaid covers
   permitted balance reads.

## 5. Architecture

```text
INGEST (GitHub Actions daily cron, no AI)
  Capitol Trades scraper / SEC EDGAR 13F parser
        │  Firebase Admin SDK writes
        ▼
FIRESTORE — system of record (Spark, server-only)
  pilot_trades → pilot_holdings → target_weights
        │
        ▼
SIGNAL (deterministic Python in Actions/local, never an LLM)
  diff target weights vs current Public holdings
  → order_batches document (status: pending)
        │
        ▼
CLAUDE (analysis and presentation only)
  summarizes batch and rationale → HUMAN APPROVES
        │ approved only; human changes batch status
        ▼
EXECUTION (workflow_dispatch, gated on status == approved)
  Public: preflight_order → place_order
  OKX: official Agent Trade Kit MCP, demo profile first
```

Deterministic code makes trading decisions. An LLM never computes position
sizes or grants approval.

## 6. Repository layout

```text
pilot-engine/
├── README.md
├── .env.example
├── firebase/
│   ├── firebase.json
│   ├── firestore.rules
│   ├── firestore.indexes.json
│   └── seed.py
├── ingest/
│   ├── capitol_trades/
│   ├── edgar_13f/
│   └── normalize.py
├── signal/
│   ├── targets.py
│   ├── diff.py
│   └── sizing.py
├── execute/
│   ├── public_client.py
│   └── approval.md
├── validate/
│   └── autopilot_diff.py
├── lib/
│   └── firestore_client.py
├── .github/workflows/
│   ├── ingest-daily.yml
│   ├── validate-weekly.yml
│   └── execute-batch.yml
└── docs/
    ├── handoff.md
    ├── source-register.md
    └── runbook.md
```

## 7. Firestore data model

Document IDs provide natural idempotency.

### `pilot_trades/{dedupe_hash}`

`dedupe_hash` is
`sha256(pilot|ticker|txn_date|txn_type|amount_low)`.

- `pilot`, `politician`, `ticker`, `asset_type`, `txn_type`: strings
- `txn_date`, `filed_date`: ISO date strings
- `amount_low`, `amount_high`: numbers
- `owner`, `source_url`, `source`: strings
- `raw`: untouched source map
- `ingested_at`: timestamp

### `pilot_holdings/{pilot}_{ticker}_{as_of}`

- `pilot`, `ticker`, `as_of`
- `weight`: number from 0 to 1

### `target_weights/{pilot}_{ticker}`

- `pilot`, `ticker`, `weight`, `computed_at`

### `order_batches/{batch_id}`

- `status`: `pending | approved | rejected | executed | failed`
- `created_at`, `decided_at`, `decided_by`
- `sleeve_notional`
- `summary_md`
- `orders`: array of `{ticker, side, notional, rationale, status,
  broker_order_id, fill_price, fill_qty}`

Status lives on the batch. Execution must reload it immediately before any
broker call.

### `validation_log/{auto_id}`

- `pilot`, `signal_date`, `diy_signal`, `autopilot_fill`
- `match`, `notes`, `created_at`

### `source_register/{source_id}`

- `name`, `url`, `type`, `reliability`, `last_ok`, `notes`

Composite indexes:

- `pilot_trades`: `pilot ASC`, `filed_date DESC`
- `pilot_trades`: `ticker ASC`, `txn_date DESC`
- `validation_log`: `pilot ASC`, `signal_date DESC`

## 8. Environment

```dotenv
FIREBASE_PROJECT_ID=
GOOGLE_APPLICATION_CREDENTIALS=
PUBLIC_API_TOKEN=
OKX_API_KEY=
OKX_SECRET_KEY=
OKX_PASSPHRASE=
QUIVER_API_KEY=
APIFY_TOKEN=
```

CI stores the complete service-account JSON in the
`FIREBASE_SERVICE_ACCOUNT_JSON` GitHub Secret and writes it to an ephemeral
runner file.

## 9. Phase plan

### Phase 0 — repository and Firebase bootstrap

Create the skeleton, deny-all rules, composite indexes, shared Admin SDK
helpers, source-register seed, scheduled stubs, manual execution gate, Python
3.12 tooling, Ruff, pytest, and emulator-backed rules tests.

Owner pre-step:

1. Create the Firebase project.
2. Create a production-mode Firestore Standard database in `us-east1`.
3. Keep Spark; do not enable Blaze.
4. Generate the service-account key and save it as the
   `FIREBASE_SERVICE_ACCOUNT_JSON` GitHub Secret.

Acceptance:

- Rules deploy and emulator tests prove client reads and writes are denied.
- CI lint and tests pass.
- No secrets are present in Git.

### Phase 1 — congressional-trade ingestion

Adapt the Capitol Trades scraper to Firestore. The dedupe hash must be the
document ID; use `set(..., merge=True)`, never `add()`. After 14 consecutive
days with no parsed documents, update `source_register` and fail loudly.

Acceptance:

- Backfill 90 days.
- Reruns create no duplicate documents.
- Simulated staleness triggers an alarm.
- Source reliability is recorded.

### Phase 2 — deterministic signal engine

Convert trades into targets and one pending order batch:

- Use disclosure-range midpoint as the position-size proxy.
- Skip orders below $5.
- Cap a single name at 5% of the sleeve.
- Process sells before buys and never exceed buying power.
- Log and skip options.

Tests cover new positions, exits, trims, minimum orders, ordering, and options.

### Phase 3 — validation

Weekly, compare proposed batches with actual Public Autopilot-sleeve fills.
Record match rate and disclosure-to-fill lag. Run for at least four weeks before
the go/no-go decision.

### Phase 4 — OKX

Create a trade-only, withdrawal-disabled API key. Validate balance and price
queries on the demo profile before creating a live profile. Keep confirmation
prompts enabled. Web3 wallets remain read-only.

Documented DCA allocation:

- BTC 40%
- ETH 30%
- SOL 10%
- UNI 10%
- ADA 10%
- Total monthly contribution: $100–200

### Phase 5 — approved execution

For an approved batch, preflight every order, then place and record fills.
Abort the entire batch if any preflight fails, the sleeve exceeds 5% of
investable assets, buying power is insufficient, or the current status is not
`approved`. The first live batch is at most $50 total.

### Phase 6 — optional E*TRADE read sync

Read-only OAuth 1.0a balance and position synchronization is optional. Order
routing remains out of scope. Vanguard and Fidelity stay manual.

## 10. Risks

| Risk | Mitigation |
|---|---|
| Scraper breaks silently | 14-day alarm; Apify and Quiver fallbacks |
| Disclosure lag | Accept as structural and measure it |
| Ranges are approximate | Midpoint proxy, documented |
| Options disclosures | Log and skip |
| Corporate actions | Preserve raw payload; manual review |
| Firestore query constraints | Declared indexes; tiny in-memory datasets |
| Unexpected billing | Spark only; no billing-dependent services |
| Tax churn | Flag at annual review |
| LLM enters execution logic | Forbidden; deterministic Python only |
| Maintenance exceeds savings | Reassess above two hours per month |

## 11. Milestones

1. Phase 0–1: bootstrap plus 90-day Firestore backfill.
2. Phase 2: first pending batch, no execution.
3. Phase 3–4: validation reports plus OKX demo.
4. Week 8+: decide whether to cancel Autopilot.
5. Month 12–18: beat VTI after all costs or wind down.

## 12. Open owner decisions

- Select a politician- or 13F-based pilot.
- Confirm options are skipped rather than track-only.
- Start with Firestore console approval or defer a Vercel UI.
- Continue or pause the $50 monthly Autopilot contribution during validation.
