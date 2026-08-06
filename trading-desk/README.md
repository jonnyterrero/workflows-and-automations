# Trading desk engine workspace

This directory is a versioned integration stub. Vendor repositories, credentials, databases, logs, and market data belong outside this hub in a separate `trading-engines` workspace.

## Create or refresh the engine workspace

From the repository root:

```powershell
# Preview without creating, cloning, fetching, or merging.
.\scripts\trading-desk\clone-engines.ps1 -WhatIf

# Default: <Programming Projects>\trading-engines
.\scripts\trading-desk\clone-engines.ps1

# Optional explicit location; it must remain outside this repository.
.\scripts\trading-desk\clone-engines.ps1 -TargetRoot 'D:\trading-engines'
```

The script manages only these directories:

- `freqtrade` — `freqtrade/freqtrade`
- `passivbot` — `enarjord/passivbot`
- `AI-Trader` — `HKUDS/AI-Trader`
- `openalgo` — `marketcalls/openalgo`
- `jesse` — `jesse-ai/jesse`
- `octobot` — `drakkar-software/octobot`
- `OpenAlice` — `TraderAlice/OpenAlice`

It intentionally excludes `ywn5124/okx-official-bot` and `Prem-ium/Auto-StockTrader`.

For an existing directory, the script verifies that it is the expected GitHub repository. A dirty worktree is left untouched. A clean worktree is fetched, but the checked-out branch is fast-forwarded only when it tracks `origin`, has no local-only commits, and can advance without a merge commit. Detached heads and branches without an `origin` upstream are fetched but not moved.

## Safety baseline

The desk convention is:

1. Backtest, simulate, analyze, or use paper/demo/testnet accounts first.
2. Keep order submission disabled until the engine-specific configuration has been reviewed.
3. Never put broker/exchange keys in this repository. Create vendor `.env`, key, and config files only inside the external engine workspace or a secret manager.
4. Bind local web/API surfaces to loopback unless remote access is deliberately secured.
5. Treat every execution-capable API, webhook, MCP tool, agent skill, and UI action as a live-order boundary unless the selected engine explicitly shows simulation mode.

This stub does not impose settings on vendor code, so each engine's runtime mode must still be verified before launch.

## Engine bootstrap and call surfaces

Upstream interfaces can change. Run installation commands from the corresponding external engine directory and re-read the linked upstream documentation after each update.

### Freqtrade

- Bootstrap: use the upstream [Docker quickstart](https://www.freqtrade.io/en/stable/docker_quickstart/) or [native installation guide](https://www.freqtrade.io/en/stable/installation/).
- Safe first run: create a user directory and config, keep `dry_run` enabled, download data, then use `freqtrade backtesting`.
- Call surfaces: the `freqtrade` CLI; optional WebUI/REST API when its API server is configured; optional Telegram control.
- Live boundary: `freqtrade trade` can place orders when dry-run is disabled and exchange credentials are configured.

### Passivbot

Bootstrap from `passivbot` using an upstream-supported Python version and Rust:

```powershell
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -e ".[full]"
passivbot backtest --help
```

- Safe first run: backtesting only. The upstream README documents backtesting and optimization but does not present a general paper-trading mode, so this desk does not treat `passivbot live` as safe.
- Call surfaces: the `passivbot` CLI, including `backtest`, optimization tools, and the execution-capable `live` command.
- Live boundary: `passivbot live ...` uses accounts from the vendor-local `api-keys.json`.
- Source: [Passivbot README](https://github.com/enarjord/passivbot#readme).

### AI-Trader

- Bootstrap: copy the vendor `.env.example` to an untracked `.env`, choose SQLite or PostgreSQL, and follow the repository's current service instructions. The top-level README does not provide a stable one-command local service launch, so none is invented here.
- Safe first run: use the platform's documented paper-trading experience; Polymarket execution is described as simulated. Confirm local behavior against the current service documentation.
- Call surfaces: FastAPI HTTP API and OpenAPI specification under `docs/api/`, agent skill files under `skills/`, and a WebSocket notification endpoint.
- Execution boundary: signal publication and copy-trading endpoints can cause followers or connected systems to act; do not equate publishing a signal with a local paper order.
- Sources: [AI-Trader README](https://github.com/HKUDS/AI-Trader#readme), [agent guide](https://github.com/HKUDS/AI-Trader/blob/main/docs/README_AGENT.md), and [OpenAPI file](https://github.com/HKUDS/AI-Trader/blob/main/docs/api/openapi.yaml).

### OpenAlgo

Bootstrap from `openalgo`:

```powershell
Copy-Item .sample.env .env
uv run app.py
```

- Safe first run: configure and verify Analyzer Mode before any broker execution. OpenAlgo documents isolated sandbox capital for this mode.
- Call surfaces: the normalized REST API under `/api/v1/`, WebSocket streaming on port `8765` by default, the web UI, webhooks, hosted Python strategies, Flow, and an MCP integration.
- Live boundary: order endpoints, hosted strategies, Flow nodes, webhooks, and MCP actions share the active broker session; adapter capabilities vary.
- Source: [OpenAlgo README](https://github.com/marketcalls/openalgo#readme) and [API documentation](https://docs.openalgo.in/api-documentation/v1).

### Jesse

- Bootstrap: follow the current [getting-started guide](https://docs.jesse.trade/docs/getting-started); Jesse's install and project workflow are version-specific.
- Safe first run: backtesting, Research API experiments, then Jesse's documented paper-trading mode.
- Call surfaces: web dashboard, Python strategies, Research API/Jupyter workflows, and the local Jesse MCP server.
- Live boundary: paper and live sessions share trading workflows, so verify the selected mode and account in the UI before starting a session.
- Sources: [Jesse README](https://github.com/jesse-ai/jesse#readme), [Research API](https://docs.jesse.trade/docs/research/), and [MCP setup](https://docs.jesse.trade/docs/mcp/setup).

### OctoBot

- Bootstrap: choose the current upstream [Python](https://www.octobot.cloud/en/guides/octobot-installation/install-octobot-with-python-and-git) or [Docker](https://www.octobot.cloud/en/guides/octobot-installation/install-octobot-with-docker-video) installation path.
- Safe first run: use the built-in simulator or backtesting before configuring an exchange account.
- Call surfaces: node/classic web interfaces, strategy and backtesting UI, and optional Telegram control. Exchange REST/WebSocket connections are configured by OctoBot rather than exposed here as a desk API contract.
- Live boundary: a manual or automated instance can submit exchange orders after live credentials and trading mode are enabled.
- Source: [OctoBot README](https://github.com/Drakkar-Software/OctoBot#readme).

### OpenAlice

Bootstrap from `OpenAlice`:

```powershell
pnpm install
pnpm dev
```

- Safe first run: read-only research, tracked entities, issues, and Inbox workflows; use simulator, paper, demo, or testnet accounts for trading experiments.
- Call surfaces: local web UI, workspace files/issues, native agent CLIs, and local market tools. Its optional Unified Trading Account and "Trading as Git" flow provide staged, reviewable, approval-gated account actions.
- Live boundary: the upstream project labels broker execution beta and experimental. Do not rely on the approval workflow as a substitute for broker-side risk controls.
- Source: [OpenAlice README](https://github.com/TraderAlice/OpenAlice#readme) and [documentation](https://openalice.ai/docs).

## Paths

Copy `paths.env.example` to `paths.env` only if a local tool needs explicit paths. `paths.env` is ignored and must not contain credentials.
