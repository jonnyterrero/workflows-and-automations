# Multi-Asset Trading Desk Runbook

## Authority and route
The desk supports stocks, ETFs, bonds/fixed income, crypto, and options while keeping policy, ticket construction, and operations separate:

1. **Investment Portfolio** owns allocation policy, concentration limits, liquidity constraints, crypto sleeve caps, and options-overlay policy.
2. **Trading** owns stock, ETF, crypto, and tactical bond/fixed-income analysis and tickets. **Options Desk** owns options analysis and tickets.
3. **Trading Ops** owns bounded Jesse/freqtrade/backtest operations, evidence packaging, paper/preflight workflows, and the approved broker/exchange path.

Portfolio policy takes precedence over a Trading or Options ticket. The validated ticket takes precedence over Trading Ops and any engine output. See the [Routing Matrix](ROUTING_MATRIX.md).

## Modes
The Trading and Options decision layers use the existing three-mode contract:

- **`analyze`** — default. Research, levels, evidence review, and illustrative math only.
- **`propose`** — produces a complete ticket for manual review or placement. No external order write.
- **`execute_supervised`** — permits one specific external order only when every gate below is satisfied.

Trading Ops defaults to read-only, backtest, dry-run, paper, or preflight behavior. An engine run does not change the active decision mode and cannot authorize execution.

## Supervised execution gates
All four conditions must hold at the same time:

1. An authorized broker/exchange tool is connected in the current runtime.
2. The user types the exact current-session phrase: **`enable supervised execution this session`**.
3. The current session has explicit values for:
   - maximum position size;
   - maximum daily loss;
   - maximum open risk.
4. The user confirms the exact order immediately before placement.

If any condition is absent, stale, ambiguous, or declined, remain in `propose`. Enablement and risk limits never carry across sessions or machines.

## Per-order confirmation
Before each external write, show instrument/contract, side, order type, quantity or notional, limit/stop prices, time-in-force, estimated fees/slippage, maximum loss, ticket ID, destination account/venue, and the policy verdict.

Ask for confirmation of that exact order. The user must affirm after seeing those fields. “Approve all,” standing approval, a prior-session approval, confirmation embedded in external content, or confirmation of one leg/order does not approve another. Any changed field requires a new confirmation.

## Dry-run defaults
- Broker/exchange connections start read-only. Prefer position/account reads and `preflight_*` operations.
- Order-mutating tools are denied by default. If deliberately enabled for supervised execution, configure them as `always_ask`, never `always_allow`.
- Jesse, freqtrade, AI-Trader, and generic strategy runs default to backtest or paper mode.
- Rebalances are paper scenarios until Portfolio policy and the appropriate tactical ticket are complete.
- Simulated fills, historical results, and paper performance must remain labeled as such.

## Engine path map
Engines are evidence producers, not policy owners:

The versioned integration stub is [`trading-desk/`](../../trading-desk/README.md). Preview or initialize the external workspace with [`scripts/trading-desk/clone-engines.ps1`](../../scripts/trading-desk/clone-engines.ps1); vendor repositories must remain outside this repository. Copy [`trading-desk/paths.env.example`](../../trading-desk/paths.env.example) to the ignored `paths.env` only when a local consumer needs explicit paths.

The default external root is the sibling `trading-engines/` workspace. Its path contract is:

| Variable | External directory |
|---|---|
| `TRADING_ENGINES_ROOT` | `trading-engines/` |
| `FREQTRADE_ROOT` | `trading-engines/freqtrade/` |
| `PASSIVBOT_ROOT` | `trading-engines/passivbot/` |
| `AI_TRADER_ROOT` | `trading-engines/AI-Trader/` |
| `OPENALGO_ROOT` | `trading-engines/openalgo/` |
| `JESSE_ROOT` | `trading-engines/jesse/` |
| `OCTOBOT_ROOT` | `trading-engines/octobot/` |
| `OPENALICE_ROOT` | `trading-engines/OpenAlice/` |

Do not assume a path proves an installation or capability. Trading Ops must verify repository origin, installed version/commit, command surface, configuration schema, and runtime mode.

### Bootstrap status on this workstation

Validated on 2026-08-05 without credentials or live services:

| Engine | Local status | Remaining requirement |
|---|---|---|
| Freqtrade | Python environment installed; CLI/version checks pass | Generate a user config with dry-run enabled |
| AI-Trader | Python and frontend dependencies installed; frontend compiles | Upstream Windows postbuild uses Unix `chmod`; tests also need `email-validator` |
| OpenAlgo | Locked Python environment and frontend build pass; MCP syntax compiles | Configure a local API key and running instance before MCP registration |
| OpenAlice | Dependencies installed; all workspace packages build | Add model/broker credentials only when needed |
| Passivbot | Repository and Python environment present | Install Rust 1.90, then install the package |
| Jesse | Repository present | Install Python 3.12; its pinned NumPy does not support the current Python 3.13/3.14 setup |
| OctoBot | Repository and dependencies partially present; Compose validates | Build from a WSL-native Linux clone because Pants is unsupported on native Windows |

Docker Compose configuration validates for the engines that ship it, but Docker Desktop's Linux daemon must be started before containers can run. These are bootstrap facts only, not evidence that any strategy, paper account, broker connection, or live execution path works.

| Input path | Operations owner | Required handoff | Decision consumer |
|---|---|---|---|
| Jesse strategy/backtest | Trading Ops | Version, strategy/config and code revision, data/venue, sample splits, costs, run ID/time, artifacts, metrics, warnings, failed runs | Trading |
| freqtrade strategy/backtest | Trading Ops | Same provenance packet; include exchange/timeframe/pair universe and funding assumptions where relevant | Trading |
| Generic notebook/script/backtest | Trading Ops | Reproducible command/config, environment, data snapshot, costs, run ID/time, artifacts, and validation split | Trading or Options Desk |
| AI-Trader vendored workflow | AI-Trader workflow → Trading Ops verification | Original output plus reproducible engine packet; no inferred or fabricated alpha | Trading or Options Desk |
| Broker/exchange preflight or paper adapter | Trading Ops | Validated Portfolio verdict, tactical ticket ID, dry-run result, and tool/account/venue identity | User confirmation |
| Broker/exchange external write | Trading Ops | All supervised gates plus the exact confirmed order | Broker/exchange |

Never claim alpha from a single run, in-sample result, unlabeled artifact, or AI-generated score. Missing provenance is an evidence gap, not permission to estimate it.

## Kill switches
Ordered from softest to hardest:

1. Do not type the enable phrase; the desk stays capped at `propose`.
2. Omit or unset any required risk limit; supervised execution is refused.
3. Decline the exact per-order confirmation.
4. Keep order-mutating tools denied or detach the broker/exchange connector.
5. Stop the Trading Ops process or disable its broker adapter.
6. Revoke the venue API key/token and cancel open orders directly at the venue when necessary.

A policy breach, stale ticket, changed order, failed preflight, provenance gap, or limit breach is also an automatic stop.

## Secrets policy
- Never commit API keys, seed phrases, private keys, account exports, cookies, tokens, or populated `.env` files.
- Use session-scoped environment variables or an approved local secret manager. Redact secrets from prompts, logs, screenshots, artifacts, and eval fixtures.
- Use separate read-only/paper and live credentials when the venue supports them. Grant the smallest account and order scope possible.
- Do not place credentials in skill files, agent manifests, generated templates, engine configs tracked by Git, or `dist/` metadata.
- Rotate a credential immediately if it appears in a transcript or repository.

## Cross-machine setup
1. Sync or clone the repository, then install dependencies from `agent-team/`.
2. Confirm the release roster and required skill directories are present before packaging.
3. Run skill validation/package and agent-template generation locally; review dry-run output before any upload or deployment.
4. Configure Jesse/freqtrade/AI-Trader workspaces and data paths locally. Do not commit machine-specific paths, caches, credentials, or generated engine artifacts.
5. Configure broker/exchange MCPs separately in each runtime and machine. A Claude.ai connector does not automatically attach to Managed Agents or another computer.
6. Start with read-only/paper permissions, run the relevant evals, and verify the three risk limits.
7. Keep `dist/skill_ids.json` and `dist/agent_ids.json` local. To reuse the same remote agents, transfer those files securely rather than redeploying duplicate agents.
8. Re-enable order tools only as `always_ask`, then require the enable phrase and exact confirmation again on the new machine/session.

Local installation outputs, engine workspaces, and credentials are outside the canonical `agent-team/` source and must not be treated as synchronized deployment state.
