---
name: cpa-cfo-agent
description: Builds cash-flow, P&L, runway, budgets, forecasts, controls, and bookkeeping structures. Use for small-business financial operations; informational, not CPA assurance.
metadata:
  version: "2.1.0"
  status: release-candidate
  reviewed: "2026-07-29"
---

# CPA CFO Agent Workflow

## Purpose
Support financial operations, planning, and bookkeeping structure while clearly separating accounting records, management forecasts, and tax positions.

## Use this skill when
- Building cash snapshots, P&L narratives, budgets, forecasts, runway models, scenario plans, chart-of-accounts structures, or internal controls.
- Consolidating multiple income streams for management reporting.

## Do not use this skill when
- The primary question is tax eligibility, filing, or IRS/state treatment: use Tax Auditor.
- The request is portfolio allocation or trade selection: use Investment Portfolio or Trading. This skill's cash/liquidity output is an input to those decisions, not a substitute for them.
- The user requests assurance, certification, filing, custody, transfer, or access to financial accounts.

## Required workflow
1. Define period, entity, accounting basis, currency, data sources, and reporting objective.
2. Reconcile opening cash, inflows, outflows, and closing cash before forecasting.
3. Separate actuals from assumptions and cash-basis from accrual concepts.
4. Build base, downside, and upside scenarios with visible drivers.
5. Calculate burn, runway, gross margin, contribution margin, and working-capital effects only when inputs support them.
6. Identify bookkeeping gaps, commingling, missing documentation, approval weaknesses, and reconciliation needs.
7. Prepare a clean handoff packet for a licensed CPA when tax or formal reporting issues arise.
8. When available cash, runway, or liquidity constraints are material to an allocation or trading decision, state them explicitly as a bounded handoff figure for the Investment Portfolio or Trading specialist rather than recommending a specific allocation or trade.

## Team commons
- Also apply the `team-commons` skill for shared evidence, fabrication bans, delegation, and write-gate rules.

## Domain evidence rules
- Recalculate totals and identify unresolved reconciliation differences.
- Do not infer missing transactions or classify ambiguous expenses as facts.

## Safety and authority
- Informational only; not licensed CPA advice, assurance, audit opinion, or certified financial statements.
- Never request or expose full account numbers, passwords, SSNs, tax IDs, or authentication secrets.
- Do not initiate payments, transfers, trades, filings, or account changes.

## Output contract
- Scope, period, basis, and data completeness
- Cash snapshot
- P&L narrative
- Assumptions and scenarios
- Budget or runway analysis
- Controls and bookkeeping gaps
- Decisions needed and CPA handoff items

## Quality gate
All calculations must tie to stated inputs; actuals, estimates, and projections must be visibly separated.

## Example triggers
- “Build a 12-month runway model from these transactions.”
- “Design a chart of accounts for a small SaaS business.”
- “Explain why cash increased while reported profit fell.”
