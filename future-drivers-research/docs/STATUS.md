# Future-Drivers Research Platform — build status

Paused mid-build. This file is the resume point.

## Decision log (settled — do not re-litigate)

**Target platform: Claude Managed Agents (CMA), not the OpenAI Agents SDK.**

The brief's §6 ("use the Agents SDK, not Agent Builder") is correct, but it is
about *OpenAI's* Agent Builder, which winds down 2026-11-30. "Claude Console
agent builder" is a different, live product: Anthropic ships Managed Agents,
buildable via Console, Claude Code, and the `ant` CLI. So the opening request
and §6 do not conflict.

CMA also satisfies §6's actual requirement — prompts, schemas, and
orchestration versioned in the repo — because agents are defined as
version-controlled YAML applied with `ant beta:agents create < agent.yaml`.
Split: **CLI owns the control plane** (agent/environment definitions),
**SDK owns the data plane** (sessions, events, tool results).

Note the existing `agent-trio/` project in this repo uses the OpenAI Agents
SDK. This is a deliberately separate stack, not a migration of it.

**Agent topology.** Agent 4 (Investment Committee) is a CMA `multiagent`
coordinator with agents 1–3 on its roster. CMA allows exactly one level of
delegation, which is precisely the brief's shape. Threads share the container
filesystem but not conversation context — so specialists write evidence files
to disk and the manager reads them. That is what lets the manager synthesize
without doing its own uncited web research (§5): its `web_search` / `web_fetch`
are disabled at the tool-config level, not merely discouraged in the prompt.

**Model:** `claude-opus-5` for all four agents.

**Secrets stay host-side.** Market/filing API keys never enter the sandbox.
Data access is via CMA *custom tools*: the agent emits `agent.custom_tool_use`,
our runner executes the call with its own credentials and returns
`user.custom_tool_result`.

**Scores are computed, not asserted.** Agents supply evidence; `fdr.scoring`
computes every number in deterministic Python. No agent is trusted to output a
score.

## Done

- `src/fdr/schemas.py` — the full §7 dossier object, plus the pieces the brief
  argues for that the original JSON sketch omitted:
  - `SourceTier` 1–5 enum, on every `Evidence` item
  - `ScoreCard` with 7 separate dimensions; `composite` exists for ranking only
    and is documented as never-display-alone (§8)
  - `Penalties` as a separate model, not folded into the quality dimensions
  - `NarrativePanel` quarantining Tier-5 sentiment out of the fundamental score
  - `DecisionJournalEntry` with a verbatim `dossier_snapshot` and outcome fields
    segregated, so look-ahead bias is structurally hard (§11)
  - `MaterialChange` for the change-detection loop (§9)

## Remaining

In rough dependency order:

1. `src/fdr/sources.py` — enforce the tier hierarchy in code: a Tier-5-only
   claim cannot raise a fundamental dimension without Tier 1–3 corroboration.
2. `src/fdr/scoring.py` — §8 weights (quality 20 / growth 20 / valuation 20 /
   financial strength 15 / proven exposure 10 / management 10 / catalysts 5)
   plus the penalty deductions.
3. `src/fdr/tools/` — host-side custom tool handlers: SEC EDGAR + FRED
   (Tier 1), market/valuation (Tier 2), portfolio overlap with ETF
   look-through, decision journal, change detection. Offline demo mode so the
   suite runs with no keys.
4. `agents/*.agent.yaml` — the four agent definitions + environment. Per-agent
   tool gating is the load-bearing part:
   - Theme Scout: web search/fetch on; explicitly forbidden from ranking
   - Evidence Analyst: filings tools + bash; no social sources
   - Risk & Valuation: market tools; structurally skeptical prompt
   - Committee Manager: read/glob/grep only, **no web tools**; coordinator roster
5. `src/fdr/runner.py` — session driver. Must get the CMA client patterns
   right: stream-first (open stream before sending), idle gate that continues
   on `stop_reason.type == "requires_action"` rather than breaking, and
   reconnect-with-history-dedupe.
6. `scripts/provision_agents.sh` — `ant beta:agents create/update` flow.
7. `tests/` + `pyproject.toml` + `README.md`.

## Environment gaps to close before a live run

None of these block the code; they block executing a real session.

- `ant` CLI not installed
- `anthropic` SDK not installed
- `ANTHROPIC_API_KEY` unset

Everything built so far is designed to be testable offline without them.
