# Deployment Status — Jonny Agent Team

**Release:** 2.1.0
**Status date:** 2026-07-30
**Local build:** green (15 skills validated + packaged)
**Live workspace state:** nothing uploaded or created yet — no API key was used in the build session

---

## What is built and verified locally

| Item | Count | Status |
|---|---|---|
| Focused skills validated + zipped | 15 | Green — `dist/skills/` + `SHA256SUMS.txt` |
| Managed Agent templates generated | 14 specialists + coordinator | Green — from `agents/manifest.yaml` |
| Eval files present | 15 | Deep Researcher and Trading expanded to 10 evals each |
| Live skill IDs | 0 | Not uploaded |
| Live agent IDs | 0 | Not created |

### New in this release
- **`deep-researcher`** — built from scratch. Opus, three modes (quick scan / standard / deep dive), per-source timestamps, per-finding confidence ratings, conflict surfacing, and a mandatory "what would change the conclusion" section. Hands off domain decisions rather than owning them.
- **`trading-agent`** — extended to three explicit modes (`analyze` / `propose` / `execute_supervised`) with four simultaneous conditions gating execution.
- **`investment-portfolio-agent`** / **`cpa-cfo-agent`** — cross-wired so CFO liquidity output is a constraint feeding allocation, and Portfolio checks Trading tickets against policy instead of re-pricing them.
- **`build_skills.py`** — added a frontmatter smart-quote check. A reformat had put U+201C/U+201D into `trading-agent`'s YAML metadata, which parses as literal curly characters rather than a quoted string; the old validator only regex-checked `name`/`description` and missed it. Verified the check catches an injected curly quote and passes clean files.

---

## Deploy sequence

Run from `agent-team/`. Set the key in your shell only — never in a repo file (this tree syncs through OneDrive).

```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-..."   # session-scoped
python -m pip install -r requirements.txt

python scripts/build_skills.py                 # 1. validate + package (green as of this doc)
python scripts/upload_skills.py                # 2. dry run — review the 15-skill plan
python scripts/upload_skills.py --execute      # 3. writes dist/skill_ids.json
python scripts/deploy_agents.py                # 4. dry run
python scripts/deploy_agents.py --execute      # 5. writes dist/agent_ids.json
```

`dist/skill_ids.json` and `dist/agent_ids.json` are gitignored, so IDs stay per-machine — expect to run the upload once per machine, or copy the JSON manually.

### Gate before the coordinator
`deploy_agents.py --execute` creates specialists **and** the coordinator in one pass. To honor the "coordinator only after specialists pass" gate, run the specialist evals in Console first, then re-run for the coordinator, or comment out the coordinator block on the first pass.

---

## MCP attachments

None are wired into the templates — they are attached per-agent in Console after creation, deliberately, so no credential ever lands in this repo.

| Agent | Needed | Notes |
|---|---|---|
| Deep Researcher | `web_search`, `web_fetch` | Already in the template; nothing to attach |
| CPA-CFO | Sheets/Drive or CSV exports | Read-only first |
| Investment Portfolio | Brokerage export / read-only positions | No trade scope |
| Trading | Broker/exchange, **read-only first** | Trade scope only after supervised dry-runs pass |

### Your Public brokerage connection
A **claude.ai connector is a different surface from a Managed Agent MCP.** Connecting Public to your claude.ai account makes it available in claude.ai chat; it does **not** attach it to the agents `deploy_agents.py` creates through the API. Those need the MCP configured on the agent definition in Console.

So the Public connection does not yet unlock `execute_supervised` — and per the plan, it shouldn't. Read-only first: use it to feed real positions into Portfolio and Trading `analyze`/`propose`, and leave execution unwired until the two gating evals pass.

E*Trade and OKX not connecting changes nothing structurally — the skill is venue-agnostic and explicitly refuses to assume a venue, custody model, or settlement mechanism you haven't stated.

---

## Trading kill switches

Ordered from softest to hardest:

1. **Say nothing** — default mode is `analyze`. Execution requires an explicit per-session enable phrase; silence means no execution.
2. **Omit a risk limit** — if max position size, max daily loss, or max open risk is unset, the skill refuses `execute_supervised` and falls back to `propose`, naming the missing limit.
3. **Decline the per-order confirmation** — each order is confirmed individually. "Approve all" is explicitly insufficient.
4. **Detach the broker MCP in Console** — removes the capability entirely, regardless of prompt content.
5. **Revoke the connector/API key** — hard stop.

A prior session's enable phrase and risk limits are never reused; both are session-scoped by design, and `adversarial-1` tests exactly that.

---

## Daily use once deployed

| Task | Agent | Mode |
|---|---|---|
| Cited research brief feeding a thesis | Deep Research Specialist | quick scan / standard / deep dive |
| Cash, runway, budget variance, decision memo | Financial Operations Specialist | — |
| Allocation, drift, concentration, rebalance plan | Portfolio Research Specialist | — |
| Chart read, no ticket | Trading Decision-Support | `analyze` |
| Full trade ticket for manual placement | Trading Decision-Support | `propose` |

Typical chain: Deep Researcher brief → Portfolio checks against strategic policy → Trading produces the tactical ticket → you place it.

---

## Remaining human steps

1. Rotate the API key that was pasted into the build session before using it (it is in the on-disk transcript).
2. Run the upload + create sequence above with the new key.
3. Run evals in Console. **Blocking for any trading execution scope:**
   - `trading-agent` `adversarial-1` — must refuse a carried-over enable phrase from a prior session
   - `trading-agent` `realistic-4` — must refuse `execute_supervised` when max daily loss is unset
   - `deep-researcher` `adversarial-1` — must refuse to fabricate a citation
   - `deep-researcher` `adversarial-2` — must ignore instructions embedded in fetched pages
4. Attach MCPs read-only; confirm tool permissions in Console match the templates.
5. Pin skill and agent versions — templates ship `version: latest`, which is fine for testing and wrong for production. Not yet pinned.
6. Add ≥5 realistic + ≥2 adversarial evals to the remaining high-risk skills (Legal, Tax, CPA-CFO, Portfolio still carry the 3-eval baseline; Deep Researcher and Trading are at 10).

---

## Known gaps

- **Versions unpinned** — `latest` throughout. Pin after eval acceptance.
- **Eval coverage uneven** — only Deep Researcher and Trading meet the ≥10 bar. Portfolio and CPA-CFO were patched for interoperability but their eval files still hold the 3-eval baseline and do not yet test the new cross-agent handoff behavior.
- **Coordinator not gated in script** — see note above.
- **Evals are unexecuted** — every eval in `evals/` is a written expectation, not a recorded pass. Nothing has been run against a live model.
- **Cursor export is current** — `sync_cursor_export.py` re-run; 15 skills + coordinator exported including `deep-researcher`.
