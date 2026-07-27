# Architecture decision record

Why this system is built the way it is. The README covers what it does; this
covers the choices behind it, including the ones that look odd without context.

## 1. Claude Managed Agents, not the OpenAI Agents SDK

**Context.** The brief said "use the OpenAI Agents SDK, not Agent Builder",
citing Agent Builder's 2026-11-30 winddown. It also opened by asking for the
Claude Console agent builder.

**Finding.** These are not in conflict. Agent Builder is OpenAI's product;
Anthropic separately ships Managed Agents, buildable via the Claude Console,
Claude Code, and the `ant` CLI, and it is current.

**Decision.** Build on Claude Managed Agents.

Managed Agents also satisfies the requirement underneath the brief's §6 —
prompts, schemas, and orchestration versioned in the repository rather than
trapped in a visual editor. Agents are persisted, versioned objects; sessions
pin to a version, so a prompt change cannot silently alter a run already in
flight.

The existing `agent-trio/` project elsewhere in this repository uses the OpenAI
Agents SDK. This is a separate stack, not a migration of it.

**Consequence.** Control plane (agents, environments) is defined as YAML and
applied by script; data plane (sessions, events, tool results) runs through the
SDK.

## 2. Four agents, one delegation level

Managed Agents permits a coordinator to delegate to a roster, but only one level
deep — a rostered agent may not itself have a roster. That is exactly the shape
the brief's process wants: a manager and three specialists, no deeper.

Threads share the session container's filesystem but not conversation context.
This turned out to be the useful property: specialists write evidence files to
`/workspace/`, and the manager reads them. So the manager can synthesise
everything the specialists found *without* being able to reach the open web
itself.

## 3. Constraints are capabilities, not instructions

The recurring decision, applied throughout.

A system prompt saying "do not perform your own web research" is a request. A
model under pressure to complete a task can talk itself past it, and nothing
catches that. The same rule expressed as an absent tool cannot be violated at
all.

Applied to:

| Rule | Enforcement |
|---|---|
| Manager does no uncited research | `web_search`/`web_fetch` absent from its tool config |
| Scout does not rank investments | No valuation or scoring tools in its roster |
| Analysts stay on primary sources | `web_search` absent; `web_fetch` retained for filings |
| No agent assigns its own score | Scoring exists only as a host-side tool that recomputes |
| Weak sourcing cannot yield high scores | `sources.gate_score` caps in code |

`tests/test_agent_definitions.py` fails if any of these are relaxed. The prompts
still explain the rules — a model that understands why a constraint exists works
with it rather than around it — but the prompt is not what holds the line.

## 4. Scores are computed, never asserted

A number produced by a language model is an opinion formatted as a measurement.
Agents supply evidence; `fdr.scoring` computes every figure.

The committee must call `score_dossier` and receives whatever the gates return.
`save_dossier` recomputes on write, so a score edited in transit does not
persist — tested in `test_stored_scores_always_match_stored_evidence`.

Two structural choices inside the scoring:

- **Risk scales the composite** rather than averaging into it, so a strong moat
  cannot offset severe leverage. Averaging would let a great business launder a
  dangerous balance sheet.
- **Penalties are held separate** from quality dimensions, so a levered,
  cyclical, high-quality business reads as exactly that rather than as
  unremarkable.

## 5. Source tiers, and what Tier 5 is allowed to do

Every citation carries a tier from 1 (SEC, Fed, Treasury, issuer holdings) to 5
(Reddit, X, YouTube, forums).

The rule: **a Tier 5 source may cause the system to investigate an asset; it may
never materially raise a fundamental score without Tier 1–3 corroboration.**

This is the platform's central claim, so it is enforced in
`sources.gate_score` — uncorroborated dimensions cap at 45, below the
advance-to-research threshold. An idea from a forum can therefore become a
watchlist candidate but not a researched conclusion, which is the correct
asymmetry. Social material is then routed into a separate narrative panel: still
visible as context and useful for spotting crowded positioning, having never
touched the fundamental score.

The Theme Scout is the one agent permitted to *lead* with Tier 4–5 material,
because hypothesis generation is its entire function.

## 6. Credentials never enter the sandbox

Data access runs as Managed Agents **custom tools**, which execute in the
orchestrator process rather than the agent container. The agent emits
`agent.custom_tool_use`; the runner dispatches through
`fdr.tools.registry.dispatch` and replies with `user.custom_tool_result`.

This matters beyond tidiness. The Evidence Analyst reads filings, and a filing
is untrusted input. If SEC or market credentials lived in the container, a
prompt injection inside a fetched document would have something to reach for.
They do not, so it does not.

Consequence: the session environment needs no open egress. `web_search` and
`web_fetch` are server-side tools running on Anthropic's infrastructure, so the
container's networking is `limited` with package managers allowed and nothing
else.

## 7. Snapshots, and the ML dataset that does not exist yet

Nothing is trained. The research reports are explicitly **not** training labels —
training on them would teach a model to reproduce the existing thesis rather
than to evaluate evidence independently.

What is being built instead is the longitudinal dataset that would justify
training later. Every `save_dossier` archives an immutable timestamped snapshot,
and every decision journal entry embeds the dossier verbatim as it stood at
decision time. Outcome fields (`forward_return`, `thesis_validated`,
`invalidation_occurred`) live in separate fields populated only by later review
passes.

The segregation is the point: a future training run reads the snapshot and
cannot see fields that did not exist yet, so look-ahead bias is structurally
awkward rather than merely discouraged.

A snapshot-collision bug found during testing — two saves in the same second
overwriting each other — is worth noting, because the failure mode was silent
loss of exactly this history.

## 8. Statuses instead of recommendations

`advance_to_deeper_research`, `watchlist_needs_trigger`, `valuation_gated`,
`exposure_not_proven`, `portfolio_overlap_concern`, `risk_exceeds_reward`,
`reject`.

These describe where a candidate sits in the process and what would move it,
which is actionable. "Strong buy" is not, and it is also the shape of output
that creates securities-law exposure (§12 of the brief). A test asserts no
status value is a trade call.

Gates are ordered most-disqualifying first, so the returned status names the
*binding* constraint. A cheap, high-quality company with unproven theme exposure
returns `exposure_not_proven` — the thing to go fix — rather than a composite
score that averages the problem away.

## 9. Runner details that are easy to get wrong

Three Managed Agents client behaviours, each of which fails quietly if missed:

- **Stream before sending.** The event stream only delivers what happens after
  it opens. Sessions are created with no initial events; the stream opens, then
  the kickoff is sent. Otherwise the opening exchange arrives as one buffered
  lump and custom tool calls inside it can be missed.
- **Idle is not done.** A session goes idle whenever it needs something from the
  client, including every custom tool call. Breaking on the first idle abandons
  the run mid-research. The loop continues while `stop_reason` is
  `requires_action`.
- **Echo `session_thread_id`.** In a multiagent session a subagent's tool call is
  cross-posted to the primary thread carrying a thread id. The reply must carry
  it back, or the result does not reach the thread waiting on it.

## 10. Deliberate exclusions

Not built, on purpose:

- Broker integration, order placement, paper trading
- Trained models of any kind
- News clustering and social sentiment pipelines
- Full-market screening; options, forex, individual corporate bonds, low-cap tokens
- A single headline score

The brief's own diagnosis was that the risk here is a large repository of
partially reliable components. One complete, trustworthy loop is worth more than
twelve partial ones, and each exclusion above is a thing that would have to be
trusted before it could be useful.
