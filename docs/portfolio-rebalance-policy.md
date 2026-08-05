# Weekly Portfolio Rebalance Policy

Standing policy for the Public.com brokerage account. Read this before executing
any weekly rebalance — it defines the targets, the bands, and the hard limits.

**Account:** `5OH85517` (BROKERAGE, CASH, options LEVEL_2)
**Cadence:** Mondays, during market hours
**Mandate:** long-term growth; harvest realized gains toward the HYSA
**Character:** experimental account, but not a trading account — this is a
buy-and-hold book that gets pruned weekly, not a strategy that turns over.

## Target allocation

| Sleeve | Target | Rebalance band | Contents |
|---|---:|---:|---|
| Broad-market core | 30% | ±5pp | VTI (~75%), VXUS (~25%) |
| Growth satellites | 35% | ±5pp | max 12 names, see cap below |
| Dividend five | 10% | ±3pp | ABBV, CVX, PG, HD, BX — one per sector |
| ETH | 15% | ±5pp | see crypto cost note |
| Cash | 10% | ±5pp | dry powder + harvest buffer |

### Position caps
- No single satellite above **5%** of total account value.
- No single satellite below **0.5%** — below that it is noise; close it or top it up.
- Satellite sleeve holds **at most 12 names**. Adding a 13th means closing one.
- The dividend five stay equal-weighted at ~2% each and hold one name per
  sector (healthcare / energy / staples / consumer / financials). Replacing a
  name means replacing it with something from the same sector.

## Rebalance procedure

1. `get_portfolio` for account `5OH85517`. Compute each sleeve as a percentage
   of `totalAccountValue`.
2. For each sleeve outside its band, compute the dollar trade back to target.
   **Sleeves inside their band are not traded.** Drift is not a reason to trade.
3. Sells first, then buys — this is a **cash account** with no margin. Buying
   power is settled cash only. Equity proceeds settle T+1.
4. Place sells, confirm fills with `get_order`, then size buys off the cash that
   actually landed — not off projected proceeds.
5. Report: what moved, what it cost, resulting allocation, and the harvest figure.

### Cash-account settlement rule
Never sell a position bought with unsettled proceeds before those proceeds
settle — that is a good-faith violation and repeated violations restrict the
account for 90 days. In practice: anything bought on a Monday must not be sold
until Wednesday. Since this is a buy-and-hold book, this rarely binds, but it
rules out same-week round trips.

## Crypto cost note — read before trading ETH

Public charges roughly **2.3% commission on crypto** (measured: $3.29 on a
$141.55 ETH sell, 2026-08-03). That is ~100x the cost of an equity trade in this
account, where reg fees run about $0.02 per order.

Consequences:
- **ETH does not get rebalanced weekly.** Only trade it when it breaks the ±5pp
  band (i.e. below 10% or above 20% of the account).
- Round-tripping ETH costs ~4.6%. Two unnecessary ETH rebalances per year wipe
  out most of a year's dividend income on a book this size.
- When ETH does need trimming, trim it all the way to target in one trade rather
  than shaving it repeatedly.

## Harvest to HYSA

The API exposes the high-yield account (`2OG64143`) as
`RESTRICTED_NO_TRADING` and provides **no transfer capability**. Moving money to
the HYSA or to outside savings is always a manual step by the account owner.

Each week, report `availableToWithdraw` minus the 10% cash target as the
"harvestable" figure, and state plainly that the transfer has to be done by hand
in the Public app. Never imply a transfer has happened.

## Hard limits

These are not defaults to be reconsidered — they are the boundary of what the
weekly routine may do without asking.

- **No options.** The account carries LEVEL_2 permissions; the weekly rebalance
  does not use them. Spreads, calls, puts, and covered calls are all out of
  scope regardless of how attractive the premium looks.
- **No shorting**, no leverage, no margin.
- **No new crypto assets** beyond ETH.
- **Max 20% of account value traded in any single week.** More than that is not
  a rebalance, it is a restructuring, and it needs sign-off.
- **No new satellite position** without the owner's approval. The weekly job
  resizes what is already held; it does not pick new stocks on its own.

## Escalate instead of acting

Stop and ask when:
- A sleeve is more than 15pp from target — something structural happened.
- Total account value moved more than 20% in a week.
- A holding is halted, delisted, or subject to a pending acquisition.
- Executing would require breaching any hard limit above.
- An order is rejected or blocked and the rebalance would be left half-applied.
  A partially executed rebalance is worse than none — report it and stop.

## History

**2026-08-03 / 08-05 — first rebalance.** Starting book was $968: ETH 29.6%,
twenty ~$5 micro-positions worth 10% in aggregate, no broad-market core, $105
idle cash. Consolidated the twenty micros into the dividend five, sold SCHO as
redundant against the HYSA, trimmed the top-heavy satellites (PANW, AVGO, GOOGL)
and the weakest theses (INTC, TEM, UBER). ETH trim to 15% was blocked at the
permission layer and left outstanding.
