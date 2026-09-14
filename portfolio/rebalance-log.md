# Portfolio Rebalance + Dividend Sweep Log

Automated weekly routine. Each entry records one run. DRY_RUN entries change nothing.

---

## 2026-09-14 (Mon) 12:05 ET — RUN STATUS: DRY_RUN

**Accounts (resolved via get_accounts):** BROKERAGE `5OH85517` (CASH), HIGH_YIELD `2OG64143`
**Pre-flight:** weekday, 12:05 ET (within 09:30–16:00), quotes fresh, no open orders. PASS.

### Snapshot
- totalAccountValue: **$847.99**
- cash: **$3.95** | buyingPower: **$3.95**
- Target sleeve held: VTI $218.04, VXUS $73.21, BIL $0.00 (34.4% of account; remaining ~65.6% is non-target equities, crypto, cash)

### Dividend sweep (trailing 7 days)
| Symbol | Amount | Date |
|--------|--------|------|
| MSFT | $0.04 | 2026-09-10 |
| CVX | $0.19 | 2026-09-10 |
| **D_total** | **$0.23** | |

Sweep S = min($0.23, $3.95 cash) = **$0.23**. No shortfall. Reserved from V (not reinvested).

### Drift analysis  (V = 847.99 − 0.23 = **$847.76**)
| Symbol | Target | Actual | Drift (pp) | Threshold | Breach |
|--------|--------|--------|------------|-----------|--------|
| VTI | 60.00% | 25.72% | −34.28 | 5.00% | YES |
| VXUS | 30.00% | 8.64% | −21.36 | 5.00% | YES |
| BIL | 10.00% | 0.00% | −10.00 | 2.50% | YES |

All three breach → full rebalance triggered.

### Trade plan (Δ = t·V − V_i; preflighted, fractional confirmed)
| Symbol | Side | Δ / OrderValue | Est. Qty | BP Req | ≤$2,500 | Placed |
|--------|------|----------------|----------|--------|---------|--------|
| VTI | BUY | $290.63 | 0.77517 | $290.63 | OK | NO (dry run) |
| VXUS | BUY | $181.12 | 2.10189 | $181.12 | OK | NO (dry run) |
| BIL | BUY | $84.78 | 0.92656 | $84.78 | OK | NO (dry run) |
| **Total** | | **$556.53** | | **$556.53** | run ≤ $10k OK | |

No sells generated (all target sleeves underweight), so no proceeds to fund the buys.

### ⚠️ Flags / errors
1. **UNFUNDABLE PLAN:** buys require **$556.53** buying power vs **$3.95** available (shortfall **$552.58**). If DRY_RUN were FALSE, all three orders would fail preflight/rejection.
2. **STRUCTURAL / CONFIG MISMATCH:** the routine measures the VTI/VXUS/BIL weights against *total* account value, but ~$600 (65.6%) of the account sits in non-target individual stocks (NVDA, AVGO, PANW, CRWD, GOOGL, AMZN, etc.) and crypto (BTC, ETH) that this spec never sells. The target sleeve is therefore permanently "underweight," producing unfundable buy orders every run. The 3-fund target cannot be reached without either (a) adding cash, or (b) a spec change that liquidates non-target positions to fund the rebalance. Needs owner decision before DRY_RUN is set FALSE.

### Sweep to HYSA
S = $0.23 > 0. No money-movement/transfer tool exists in the Public MCP.
**MANUAL ACTION: transfer $0.23 from brokerage `5OH85517` to HYSA `2OG64143`** (dividends: MSFT $0.04 + CVX $0.19).

### Result
- RUN STATUS: DRY_RUN (no orders placed, nothing changed)
- NEXT RUN: 2026-09-21 (Mon)
