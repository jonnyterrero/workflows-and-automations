# Deployment Status — Priority Four

**Status date:** 2026-07-29
**Release:** 2.1.0
**Scope of this pass:** Deep Researcher (new), Trading (3-mode rewrite), Investment Portfolio + CPA-CFO (interop patches).

## What is done (verified locally)

| Item | State | Evidence |
|---|---|---|
| `deep-researcher` skill | Created | `skills/deep-researcher/SKILL.md`, packaged OK |
| `deep-researcher` agent template | Generated | `agents/deep-researcher.template.yaml` (Opus 5, research tool profile) |
| Trading 3 modes (`analyze`/`propose`/`execute_supervised`) | Implemented | `skills/trading-agent/SKILL.md` — Modes section + gates |
| Portfolio ↔ Trading ↔ CFO interop | Implemented | Cross-reference steps added to all three skills |
| Routing matrix updated | Done | `docs/ROUTING_MATRIX.md` — Deep Researcher row + trading gate language |
| Eval suites | Expanded | deep-researcher, trading, cpa-cfo, investment-portfolio = 10 evals each (3 baseline + 5 realistic + 2 adversarial) |
| Skill packaging | Passing | `python scripts/build_skills.py` → 15 skills OK, `dist/skills/SHA256SUMS.txt` written |
| Template generation | Passing | `python scripts/generate_agent_templates.py` → 14 specialists + coordinator |
| Upload / agent creation | **NOT DONE** | No `ANTHROPIC_API_KEY` in the build environment; both scripts dry-run only |

**Nothing has been uploaded to your Anthropic workspace and no Managed Agents have been created.** Every ID below is still a placeholder.

## Local verification already run

```bash
cd agent-team
python scripts/generate_agent_templates.py   # 14 specialists + coordinator, release 2.1.0
python scripts/build_skills.py               # 15 skills OK + SHA256SUMS.txt
python scripts/upload_skills.py              # dry run: 15-skill plan
python scripts/deploy_agents.py              # dry run: 14 specialists + coordinator
```

One validation failure was found and fixed during this pass: the rewritten Trading description exceeded the 200-char Claude.ai limit (254). It is now 172.

## Your run order (execute in sequence)

Requires `ANTHROPIC_API_KEY` for a workspace where you intend these to live.

```bash
cd agent-team
python -m pip install -r requirements.txt

export ANTHROPIC_API_KEY=...        # PowerShell: $env:ANTHROPIC_API_KEY="..."

# 1. Re-verify packaging
python scripts/build_skills.py

# 2. Review the plan, then upload the 15 skills
python scripts/upload_skills.py
python scripts/upload_skills.py --execute
#    → writes dist/skill_ids.json  (gitignored, per-machine)

# 3. Review, then create 14 specialists + coordinator
python scripts/deploy_agents.py
python scripts/deploy_agents.py --execute
#    → writes dist/agent_ids.json  (gitignored, per-machine)
```

If you only want the priority four first, upload all 15 skills anyway (they are cheap and `team-commons` is a dependency of every agent), but create agents selectively in Console instead of running step 3 — use the four templates directly:
`agents/deep-researcher.template.yaml`, `cpa-cfo-agent.template.yaml`, `investment-portfolio-agent.template.yaml`, `trading-agent.template.yaml`.

**Do not run step 3 until specialist skills pass their evals** (see below). The coordinator's roster is built from whatever specialists exist at creation time.

## Gate: run evals before trusting any agent

`evals/*.json` are eval *definitions*, not an automated runner — there is no local harness in this package. Run them manually in Console against each created agent and record pass/fail. Minimum bar before daily use:

- All 3 baseline evals pass per agent.
- For the four priority agents: all 10 pass, and **both adversarial cases must pass** — these encode the safety boundary, not style.
- Trading `adversarial-1` (stale session enable phrase) and `realistic-4` (missing risk limit) are the two that must never regress. If either fails, do not attach a broker MCP.

## Model choices

| Agent | Model | Why |
|---|---|---|
| Deep Researcher | `claude-opus-5` | Multi-source conflict detection and confidence calibration are the failure-prone parts; this output feeds every other specialist |
| CPA-CFO | `claude-sonnet-5` | Structured reconciliation against supplied inputs; deterministic enough for Sonnet |
| Investment Portfolio | `claude-sonnet-5` | Diagnostics over provided holdings; escalate to Opus if thesis quality disappoints |
| Trading | `claude-sonnet-5` | Ticket construction is procedural; the safety-critical parts are gates, not reasoning depth |
| Coordinator | `claude-opus-5` | Routing + synthesis across 14 specialists |

## MCP / connection plan

Nothing here is wired yet — attach in Console, least privilege, one agent at a time.

| Agent | Attach | Order |
|---|---|---|
| Deep Researcher | `web_search`, `web_fetch` (already in template) | Ready now, no external creds |
| CPA-CFO | Sheets/Drive or CSV exports, **read-only** | After baseline evals |
| Investment Portfolio | Brokerage CSV export or read-only portfolio API | After baseline evals; **no trade scope** |
| Trading | Exchange/broker MCP **read-only first** | Only after all 10 trading evals pass |

Trading write/trade scope is a separate, later decision. Read-only first, supervised dry-runs next, trade perms last.

## Operating runbook — the four priority agents

### Deep Researcher
- **Invoke:** "Standard research: …" / "Quick scan: …" / "Deep dive: …" (state the mode or it defaults to standard).
- **Autonomous:** search, fetch, synthesize, rate confidence.
- **Needs your OK:** nothing for read-only research; `bash` is `always_ask`.
- **Failure mode:** confident synthesis over thin sources. Mitigation — check the confidence column and the "what would change the conclusion" section before acting on it.

### CPA-CFO
- **Invoke:** "Build a runway model from these actuals", "Why did cash rise while P&L fell?", "Management report vs forecast".
- **Autonomous:** reconciliation, scenarios, variance, controls gaps.
- **Needs your OK:** nothing autonomous touches money. It never pays, transfers, or files.
- **Failure mode:** silently assuming missing transactions. Mitigation — it must list unresolved reconciliation gaps; if it doesn't, the answer is incomplete.

### Investment Portfolio
- **Invoke:** "Allocation and drift vs my targets", "Is my crypto weighting too high given X horizon", "Does this Trading ticket violate policy?"
- **Autonomous:** diagnostics, drift, concentration flags, rebalance *plans*.
- **Needs your OK:** every actual trade — it produces tickets, you place them.
- **Failure mode:** inventing holdings/constraints you didn't supply. Mitigation — it should ask once, then label assumptions explicitly.

### Trading
- **Invoke:** state the mode. "Analyze this chart" → `analyze`. "Propose a ticket" → `propose`. Execution requires the explicit enable phrase.
- **Autonomous:** `analyze` and `propose` only.
- **Needs your OK:** `execute_supervised` requires all four simultaneously — connected broker/exchange tool, session enable phrase typed *this session*, per-order confirmation, and configured max position size / max daily loss / max open risk.
- **Kill switches:**
  1. Don't type the enable phrase → mode caps at `propose`.
  2. Detach the broker/exchange MCP in Console → execution impossible regardless of prompt.
  3. Unset any risk limit → refuses `execute_supervised`, falls back to `propose`.
  4. Revoke the exchange API key at the venue → hard stop outside Claude entirely.
- **Failure mode:** prompt-injected or social-engineered execution. Mitigation — enable phrase and per-order confirmation are session-scoped and never inherited; adversarial-1 tests exactly this.

## Remaining human steps

1. Set `ANTHROPIC_API_KEY` and run the upload/deploy sequence above.
2. Run evals per agent; record pass/fail. Do not skip the two adversarial cases on the finance/trading agents.
3. Attach MCPs read-only, one agent at a time.
4. Pin skill and agent versions after acceptance — templates currently use `version: latest`, which is fine for bring-up and **not** fine for steady state.
5. Set the three trading risk limits explicitly before ever enabling supervised execution.
6. Create the coordinator last, only after the specialists pass.

## Known gaps

- No automated eval runner in this package; evals are manual Console definitions.
- `execute_supervised` has no broker adapter — the mode's gates are specified and enforced in the skill, but the actual order-placement tool is not attached and not written. That is deliberate: the tool arrives with your credentials, not from this repo.
- Remaining 10 specialists still have only the 3 baseline evals each.
- The 4 non-priority high-risk agents (legal, tax) were not expanded in this pass.
