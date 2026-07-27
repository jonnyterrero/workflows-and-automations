# Future-Drivers Investment Research Platform

> Research and decision support only. This platform does not provide personalised
> financial advice, hold funds, pool capital, or execute trades. Every decision
> requires human review. See [Legal posture](#legal-posture).

A four-agent research loop on **Claude Managed Agents** that helps a small group
discover important companies and technologies early, test those ideas against
evidence, manage concentration risk, and make more disciplined long-term
decisions.

The loop it implements:

```
discover candidate → prove thematic exposure → analyse financial quality
→ test valuation → construct bear case → evaluate portfolio fit
→ record human decision → monitor what changed → review outcome
```

## The four agents

| # | Agent | Does | Deliberately cannot |
|---|-------|------|---------------------|
| 1 | **Theme Scout** | Detects technologies, capex cycles, and policy shifts; maps them to candidate companies and funds | Rank, score, or value anything |
| 2 | **Evidence Analyst** | Proves or disproves theme exposure from SEC filings; computes fundamentals | Search the web; use social sources |
| 3 | **Risk & Valuation Analyst** | Tests embedded expectations, builds the bear case, defines invalidation conditions | Search the web; assign final scores |
| 4 | **Investment Committee Manager** | Coordinates the three, reconciles disagreements, produces the research card | **Do any web research of its own**; assign its own scores |

Agent 4 is a Managed Agents `multiagent` coordinator with 1–3 on its roster.
Managed Agents permits exactly one level of delegation, which is the shape this
process wants. Threads share a filesystem but not conversation context, so
specialists write evidence to `/workspace/` and the manager reads it.

## Why Managed Agents

Anthropic ships Managed Agents — buildable via the Claude Console, Claude Code,
and the `ant` CLI — where Anthropic runs the agent loop and hosts a per-session
sandbox. Agents are persisted, versioned objects; sessions pin to a version.

This is a different product from OpenAI's Agent Builder (which winds down
2026-11-30). It also keeps prompts, schemas, and orchestration in this
repository rather than in a visual editor: agent definitions live in
[`agents/`](agents/) as YAML, and every tool schema lives in code.

The split is **CLI/scripts own the control plane** (agent and environment
definitions) and **the SDK owns the data plane** (sessions, events, tool
results).

## Quick start

Everything below runs offline against fixtures. No API key, no network.

```bash
cd future-drivers-research
make setup
make test        # 145 tests
make validate    # check agent definitions
```

To run live:

```bash
cp .env.example .env      # add ANTHROPIC_API_KEY, set FDR_DEMO_MODE=false
make provision            # creates the 4 agents + environment, prints their IDs
# paste the printed IDs into .env
make run SYMBOL=NVDA
make changes SYMBOL=NVDA  # what moved since the last review
```

`make provision-dry` prints the exact payloads without calling the API.

## Design constraints, and why they are in code

The value of this system is that it can be trusted repeatedly. Where a rule
mattered, it is enforced structurally rather than requested in a prompt — a
prompt instruction is a request, and a model can be argued out of it.

**Source tier hierarchy.** Every piece of evidence carries a tier, 1
(SEC/Fed/Treasury) to 5 (Reddit/X/YouTube). A Tier 5 source may cause the
system to *investigate* an asset; it can never materially raise a fundamental
score without Tier 1–3 corroboration. `fdr.sources.gate_score` caps
uncorroborated dimensions at 45 regardless of how confidently an agent argues
for 95. Social material is routed to a separate narrative panel, visible as
context, having never touched the score.

**Agents do not produce scores.** They supply evidence; `fdr.scoring` computes
every number. The committee must call `score_dossier` and receives whatever the
gates return, including outcomes it did not want. `save_dossier` recomputes on
write, so a tampered score cannot be persisted.

**Nothing collapses to one number.** A `ScoreCard` carries seven dimensions —
quality, growth, valuation, financial strength, evidence confidence, risk,
portfolio fit. "85 quality / 25 valuation" tells you what to do; "73" does not.
Risk *scales* the roll-up rather than averaging into it, so a strong moat cannot
offset severe leverage.

**Capability withholding.** The committee manager has no `web_search` and no
`web_fetch`, so "synthesise evidence, don't do your own uncited research" is a
fact about its configuration. The Scout has no valuation tools, so "don't rank
candidates" is likewise structural. Tests fail if anyone re-enables them.

**Statuses are process states, not calls.** `advance_to_deeper_research`,
`watchlist_needs_trigger`, `valuation_gated`, `exposure_not_proven`,
`portfolio_overlap_concern`, `risk_exceeds_reward`, `reject`. Gates are ordered
most-disqualifying first, so the returned status names the binding constraint.
There is no buy, sell, or price target anywhere in the system.

**Credentials never enter the sandbox.** SEC, FRED, and market access run as
Managed Agents *custom tools*, which execute in the orchestrator process. The
agent asks; we make the call. A prompt injection inside a fetched filing cannot
reach a key that was never in the container.

**Unknown is not zero.** A company that does not disclose a figure is recorded
as not disclosing it. Undisclosed values are never silently coerced to zero,
because "did not say" and "said zero" are different facts.

## Layout

```
agents/                     Agent definitions — prompts and built-in tool gating
  theme-scout.agent.yaml
  evidence-analyst.agent.yaml
  risk-valuation-analyst.agent.yaml
  investment-committee.agent.yaml
  research.environment.yaml
src/fdr/
  schemas.py                Dossier, evidence, scorecard, decision journal
  sources.py                Tier hierarchy and score gating
  scoring.py                Weights, penalties, status gates
  definitions.py            Joins YAML prompts to registry tool schemas
  runner.py                 Session driver (stream-first, custom-tool loop)
  tools/
    registry.py             Canonical tool contract + dispatch
    filings.py              SEC EDGAR            (Tier 1)
    macro.py                FRED                 (Tier 1)
    market.py               Market data + ratio arithmetic (Tier 2)
    portfolio.py            ETF look-through and concentration
    journal.py              Dossier snapshots + decision journal
    changes.py              Material change detection
config/themes.yaml          Initial thematic universe and exclusions
scripts/                    provision_agents.py, run_research.py
```

Agent YAML holds what a human writes (prompt, model, built-in tools); the
registry holds custom tool JSON schemas, which must match handler signatures.
Neither duplicates the other, so they cannot drift.

## Scoring model

| Dimension | Weight |
|---|---|
| Business quality and moat | 20% |
| Growth durability | 20% |
| Valuation and expectations | 20% |
| Financial strength | 15% |
| Proven thematic exposure | 10% |
| Management and capital allocation | 10% |
| Catalysts and revisions | 5% |

Separate penalties: leverage, dilution, cyclicality, customer concentration,
regulatory, geographic, source weakness, stale data, crowded expectations.
Source weakness and staleness are computed from the evidence base; the rest are
the Risk Analyst's measured judgement.

News, technical momentum, and social sentiment are absent by design.

## Asset universe

US-listed stocks and ETFs, BTC and ETH, Treasury and bond ETFs, gold and silver
ETFs. Explicitly out of scope for now: individual corporate bonds, options,
forex, low-cap tokens, automated execution, full-market screening. See
[`config/themes.yaml`](config/themes.yaml).

## Legal posture

The first product sits firmly on the research and education side:

- Each user keeps their own brokerage account
- The platform produces general research and evidence
- Users make their own decisions; nothing is executed automatically
- No pooled funds, no custody, no transaction-based compensation
- No guaranteed or personalised return claims

The SEC analyses investment-adviser status around providing securities advice,
for compensation, as a business, and construes those elements broadly — a
disclaimer alone does not change the substance of a service. Pooling money
creates a separate investment-club analysis.

**Before** charging users, offering individualised portfolio recommendations,
pooling capital, or enabling execution, get securities-law review. This is not a
reason to stop building; it is a reason to keep the first product where it is.

## Roadmap

Phase 1 (this repository) is the complete research loop. Deliberately excluded
until it is reliable:

- **Phase 2** — ETF look-through at portfolio level, scenario analysis, rebalancing
- **Phase 3** — news clustering, narrative analysis, patent/contract/policy monitoring
- **Phase 4** — point-in-time backtesting on the accumulated snapshots, then narrow
  models (does this deserve research? is exposure genuine?), each benchmarked
  against equal-weight and rule-based baselines
- **Phase 5** — paper trading, then human-approved execution with hard limits

On ML specifically: nothing is trained yet, and the research reports are not
training labels — training on them would teach a model to reproduce the existing
thesis rather than to test it. The decision journal is accumulating the
longitudinal dataset instead, with outcome fields structurally segregated from
the point-in-time snapshot so look-ahead bias is hard to introduce.
