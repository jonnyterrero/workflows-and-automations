# Approval gate

Pilot Engine is recommend-only. A generated order remains `pending` until the
owner reviews the complete batch and gives fresh, explicit approval.

Execution code must:

1. Load every order in the requested batch.
2. Refuse the batch unless every executable row is `approved`.
3. Re-run all portfolio, sleeve-cap, and buying-power preflights.
4. Abort the whole batch when any preflight fails.
5. Record each attempted result in `order_executions`.

Approval is batch-specific and cannot be inferred from prior approvals,
messages, schedules, or an LLM response. Rejected, stale, partially approved,
or modified batches must not execute.
