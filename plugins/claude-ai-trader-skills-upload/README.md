# AI-Trader Portable Skills

Six vendored AI-Trader reference skills for Cursor and Claude Code, adapted with team-commons supervised-write gates. Read-only market and platform discovery is allowed. External writes require execute_supervised, explicit current-session enablement, and confirmation for each action.

## Installation

- Cursor: install this folder as a local plugin. Cursor reads .cursor-plugin/plugin.json and the relative skills/ directory.
- Claude Code: upload or install this folder through the local plugin workflow. Claude Code reads .claude-plugin/plugin.json and discovers skills/.
- Keep the team team-commons skill available. If it is unavailable, these skills must remain read-only.

## Skills

- ai4trade - platform bootstrap and API routing
- ai4trade-copytrade - provider discovery and supervised follow/copy actions
- ai4trade-tradesync - supervised signal and trade synchronization
- ai4trade-heartbeat - notification reads and supervised state-changing polling/messages
- ai4trade-market-intel - read-only market intelligence
- ai4trade-polymarket - public Polymarket reads and supervised AI-Trader publishing

## Usage

Invoke a skill by name or ask for the matching AI-Trader task. Reads may proceed directly. For a write, the agent must first present a redacted action preview and satisfy all safety gates in that skill. Tokens and passwords must be supplied only at runtime through an approved secret source and must never be saved in this bundle.

See upstream.json for the exact source revision and path mapping.
