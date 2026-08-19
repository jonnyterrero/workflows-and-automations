# Runbook

## Current state

- Phase: 0 — Firebase infrastructure bootstrap
- Backend: Firestore Standard edition on Firebase Spark
- Trading mode: disabled
- Ingestion mode: no-op stub
- Pilot: not yet confirmed; Phase 1 is blocked until the owner selects a
  politician- or 13F-based pilot
- Options: log and skip; no options execution
- Approval UI: Firestore console status flip to start

## Owner Firebase setup

1. Create a Firebase project and a production-mode Firestore Standard database
   in `us-east1`.
2. Keep the project on Spark. Do not enable Functions, Scheduler, Storage, or
   Blaze.
3. Generate a service-account private key.
4. Store the complete JSON as the GitHub Secret
   `FIREBASE_SERVICE_ACCOUNT_JSON`.
5. Delete unneeded local copies after configuring the secret.

Never paste the key into source code, an issue, a pull request, or chat.

## Local verification

```bash
uv sync --locked
uv run ruff check .
npx -y firebase-tools@latest emulators:exec \
  --only firestore \
  --project demo-pilot-engine \
  --config firebase/firebase.json \
  "uv run pytest"
```

The `demo-` project ID guarantees emulator-only Firebase access. Phase 0 tests
verify that unauthenticated client reads and writes are denied.

## Deploy rules and indexes

After authenticating the Firebase CLI and selecting the intended project:

```bash
npx -y firebase-tools@latest deploy \
  --only firestore:rules,firestore:indexes \
  --project "$FIREBASE_PROJECT_ID" \
  --config firebase/firebase.json
```

Review the project ID in the command before deploying. Admin SDK operations
bypass Firestore Security Rules; only trusted server-side jobs may receive the
service account.

## Seed the source register

Set `FIREBASE_PROJECT_ID` and `GOOGLE_APPLICATION_CREDENTIALS` to the intended
project and local service-account path, then run:

```bash
uv run python firebase/seed.py
```

The seed uses deterministic source IDs and is safe to rerun.

## Scheduled jobs

- `ingest-daily.yml`: daily cron plus CI tests; ingestion is a Phase 0 no-op.
- `validate-weekly.yml`: weekly cron; validation is a Phase 0 no-op.
- `execute-batch.yml`: manual dispatch only. It fails unless the requested
  Firestore batch currently has status `approved`; Phase 0 then stops without
  calling a broker.

## Secrets

Create `.env` locally from `.env.example` and never commit it. OKX credentials
must be trade-scoped, withdrawal-disabled, and validated against the demo
profile before any live profile is created. Vanguard and Fidelity credentials
are permanently out of scope.

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
