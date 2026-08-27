# Public.com Rebalancer — Discovery Notes (WIP)

> Status: **brainstorming, incomplete.** Design not yet presented or approved.
> No spec written, no code written. Resume from "Next Session" at the bottom.
> Date of session: 2026-08-01

This platform provides research and decision-support only. It does not provide
personalized financial advice. All trade decisions require human review and
manual execution.

---

## 1. Scope

Add an allocation + rebalancing module for the **Public.com** brokerage account,
covering two discretionary sleeves:

- `PUBLIC_CRYPTO_AGGRESSIVE` — ETH-ecosystem / smaller alts, satellite to the OKX core
- `PUBLIC_STOCKS_AGGRESSIVE` — growth names outside the ring-fenced tracker

Capital: **~$50 biweekly** (~$100/mo), configurable as `DEPOSIT_AMOUNT` /
`DEPOSIT_CADENCE`. Default sleeve split `CRYPTO_STOCK_SPLIT` = 40 / 60.

**Out of scope:** OKX (separate core, never touched by this system), options,
leverage, tax advice.

---

## 2. Decisions locked this session

| # | Decision | Choice |
|---|---|---|
| D1 | Where the code lives | **Module inside `trading-intelligence-agent`**, not standalone. New `packages/` alongside existing ones. |
| D2 | v1 execution model | **Proposal file + manual entry.** Engine emits signed, timestamped order tickets; user places trades in the Public app. No API order submission in v1. |
| D3 | Ring-fenced sleeve | **Cohort A (opened 2026-07-14) is the Pelosi tracker.** Engine must never propose trades against it. |

### Consequences of D1
Reuse rather than rebuild:
- `packages/policy/` — `evaluate_portfolio_decision` → `allow`/`warn`/`block` is the approval gate
- `packages/risk_engine/risk_flags.py` — vol thresholds, crypto hype detection
- `packages/storage/` + alembic — state and migrations
- `apps/scheduler_service/` — weekly drift check
- `apps/api_service/` + static dashboard — reporting surface
- `PortfolioRiskBucket.AGGRESSIVE` and theme-tagged `ASSET_UNIVERSE` already exist in `packages/policy/defaults.py`

### Consequences of D3
Discretionary (in-scope) holdings are therefore:
- **Stocks:** Cohort B only — the twenty $5.00 positions, **$98.69**
- **Crypto:** ETH, **$287.86**
- **Cash:** $104.94, shared (see F3)

Ring-fenced (untouchable): Cohort A, **$477.63**, including `SCHO`.

---

## 3. Findings from the live account

Pulled 2026-08-01 via Public.com MCP. Account `5OH85517` (BROKERAGE);
`2OG64143` (HIGH_YIELD) also exists.

Totals: **$969.12** — stocks $576.32 (59.5%), crypto $287.86 (29.7%), cash $104.94 (10.8%).

### F1 — `strategyIds` is empty on all 33 positions ⚠️ load-bearing
Public's API does **not** tag which positions belong to which strategy or
Investment Plan. Sleeve attribution **cannot be derived programmatically.**

→ A user-maintained **ownership manifest** (symbol → sleeve) is a first-class
component. The engine must **fail closed**: any position it cannot attribute
blocks the run rather than defaulting to in-scope.

### F2 — Two cohorts, cleanly separated by `openedAt`

| Cohort | Date | N | Value | Symbols |
|---|---|---|---|---|
| **A** (ring-fenced) | 2026-07-14 | 13 | $477.63 | AVGO, PANW, GOOGL, AMZN, CRWD, INTC, VST, NVDA, AAPL, TEM, SCHO, MSFT, UBER |
| **B** (discretionary) | 2026-07-27 | 20 | $98.69 | MO, PM, KO, PEP, PG, VZ, XOM, CVX, MRK, PFE, ABBV, BMY, ABT, AMGN, MDT, MCD, HD, SO, BX, COP |

Cohort B is 20 positions at **exactly $5.00 cost basis each**, same day —
machine-generated, not hand-placed.

### F3 — Cash is a single shared pool
$104.94, no segregation between sleeves. Requires **virtual sleeves with
reserved cash pools** in the state model; buying power is a shared constraint
that both sleeves draw against.

### F4 — Crypto satellite is greenfield
ETH is the *only* crypto position — 100% of the sleeve. Building
`PUBLIC_CRYPTO_AGGRESSIVE` is a construction problem, not a rebalancing one.

### F5 — The API's own percentages disagree ⚠️
Position-level `percentOfPortfolio` divides by **~$1,269.20**; the `equity`
block divides by **$969.12**. The ~$300 delta is likely the HIGH_YIELD account
leaking into the denominator.

→ **Never trust `percentOfPortfolio`.** Compute all weights from dollar values
against an explicitly chosen denominator. Trusting the API field would have
introduced a silent ~30% weighting error.

### F6 — `get_all_instruments` is unreliable ⚠️
Failed 3× (`API Error 400: Unknown error` twice, then a connector timeout),
with and without `type_filter` / `trading_filter`.

→ The "never invent tickers / verify against live listings" requirement has no
reliable data source yet. **Needs a spike** before any crypto universe is
hardcoded. Fallback: probe `get_quotes` per candidate symbol and treat a
successful quote as the listing test. Cache results with a TTL.

---

## 4. Design tension to resolve (raised, not settled)

Given D3, the discretionary stock sleeve is **$98.69 of defensive dividend
names** (tobacco, staples, pharma, energy, utilities). Reaching an
"aggressive growth" target from that base implies near-total turnover — which
collides with "human-in-the-loop for all sells" and generates ~20 small-dollar
sells with tax lots.

**Cash-flow rebalancing is the strong alternative.** At ~$100/mo of new
deposits against a ~$99 sleeve, new money alone can reshape the sleeve within
months **without a single sell** — no realized gains, no wash-sale exposure, no
sell-approval friction. Deposits are the primary rebalancing instrument at this
account size; sells become the exception path, not the norm.

This should be the default rebalancing mode in the design.

---

## 5. Boundaries held

- **Engine, not picks.** Target weights, sleeve bands, and the candidate
  universe are user-supplied config. Assistant implements and validates them;
  it does not originate "buy these names at these weights." Consistent with the
  existing repo README's decision-support-only stance.
- **No assistant-executed trades.** The system may be *built* to submit orders
  (post-v1, behind a flag), but the assistant will not place them via MCP.

---

## 6. Open items

1. **The requirements prompt was truncated** mid-sentence at
   `## 1. Architecture (build this)`. Sections 1–N of SYSTEM REQUIREMENTS were
   never received. **Ask user to re-paste.** Received in full: GOALS,
   CAPITAL & CONSTRAINTS, PORTFOLIO PHILOSOPHY.
2. Confirm Cohort B is genuinely discretionary and not a second automated plan
   (its uniformity suggests automation — worth a sanity check).
3. Decide the drift trigger: relative band (%) vs absolute ($) vs both. At
   ~$99 sleeve size, a 5% relative band is ~$5 — likely too tight to be
   meaningful; absolute floors matter more at this scale.
4. Minimum order size / fractional granularity on Public — verify.
5. Crypto spread modeling as a cost input (Public crypto is spread-based).
6. Whether the HIGH_YIELD account (`2OG64143`) participates at all.

---

## 7. Next session

1. Get the truncated requirements section from the user.
2. Finish brainstorming: propose 2–3 architectural approaches, present design
   in sections, get approval per section.
3. Spike `get_quotes`-based universe validation (F6) — this gates the crypto
   sleeve entirely.
4. Write the approved spec to
   `docs/superpowers/specs/YYYY-MM-DD-public-rebalancer-design.md`, run the
   spec-review loop, then move to `writing-plans`.

**Do not write implementation code until the design is approved.**
