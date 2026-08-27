## Learned User Preferences
- Default trading automation to paper or decision-support workflows; live execution must be supervised, enabled for the current session, and confirmed per action.
- Keep full external vendor and trading-engine clones outside this workflows hub; sync only portable skills, adapters, and thin integration stubs through the repository.
- Treat this repo as the only live checkout of the hub; do not recreate numbered sibling clones under `integrations&automations`.
- Claude platform skill-upload zips must have `SKILL.md` at the archive root, not nested under a skill-named folder.

## Learned Workspace Facts
- `agents/agent-team/` is the canonical source for specialist skills, roster metadata, routing rules, evaluations, and local Cursor/Claude exports.
- The trading desk uses Freqtrade, Passivbot, AI-Trader, OpenAlgo, Jesse, OctoBot, and OpenAlice as external runtimes; the affiliate-only OKX repository and Auto-StockTrader are intentionally excluded.
- Hub top-level layout is `plugins/`, `agents/`, `trading/`, `automations/`, `projects/`, `docs/`, `config/`, and `scripts/`; keep plugin-upload bundles and nested stacks in those folders rather than at the repo root.
- Claude-uploadable engineering skill packs live in the sibling `Skills for AI's` directory, not in this hub.
