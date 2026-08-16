# Approval gate

Pilot Engine is recommend-only. A generated `order_batches` document remains
`pending` until the owner reviews the complete batch and gives fresh, explicit
approval by changing the batch status in the Firestore console.

Execution code must:

1. Load the requested batch from Firestore at execution time.
2. Refuse the entire batch unless its current status is exactly `approved`.
3. Re-run all portfolio, sleeve-cap, and buying-power preflights.
4. Abort the whole batch when any preflight fails.
5. Record fills in the batch's `orders` array and set the batch status.

Approval is batch-specific and cannot be inferred from prior approvals,
messages, schedules, or an LLM response. Rejected, stale, partially approved,
missing, or modified batches must not execute. The `execute-batch` workflow can
only be started manually with `workflow_dispatch` and rechecks Firestore before
continuing.

Phase 0 stops after that status check and makes zero brokerage calls.
