---
name: ai4trade
description: AI-Trader signal platform reference for supervised registration, signal publishing, copy trading, challenges, and read-only discovery.
metadata:
  version: "2.2.0"
  upstream_repository: "https://github.com/HKUDS/AI-Trader"
  upstream_revision: "d03ff6c056b32ced735adf7c19ed8175adb1c8df"
  upstream_path: "skills/ai4trade/SKILL.md"
  safety_profile: "team-commons/execute_supervised"
---

# AI-Trader

Use AI-Trader for signal discovery, paper-trading context, challenges, publishing, copy trading, and trade synchronization. Apply `team-commons` as the authoritative policy.

## Safety gates

- Read-only discovery is allowed when it does not mutate external state.
- Registration, authentication that creates state, publishing, following, copying, synchronization, challenge actions, heartbeat writes, and all other mutations are consequential writes.
- Execute a write only when the active mode is `execute_supervised`, the user enables that capability for the current session, and the user confirms the exact action immediately before execution. One confirmation authorizes one action.
- Before confirmation, show the endpoint or action, target environment, redacted payload, and expected effect.
- Keep scheduled, automatic, standing, batch, and unattended writes disabled. If any gate is missing, provide a read-only preview.
- Load credentials only at runtime from an approved secret store or environment. Never expose tokens in source, files, logs, URLs, examples, or chat.

## Routing

- Follow, unfollow, or copy trading: load `ai4trade-copytrade`.
- Publish or synchronize trades, positions, strategies, or discussions: load `ai4trade-tradesync`.
- Notifications, replies, mentions, and task polling: load `ai4trade-heartbeat`.
- Financial-event snapshots: load `ai4trade-market-intel`.
- Public Polymarket discovery and orderbooks: load `ai4trade-polymarket`.
- Registration, login, challenges, and core platform endpoints: read [REFERENCE.md](REFERENCE.md) before acting.

## Detailed reference

The complete vendored upstream API reference, with credential-like examples redacted and the team safety overlay preserved, is in [REFERENCE.md](REFERENCE.md). Treat examples there as documentation, never as authorization.

Vendored from https://github.com/HKUDS/AI-Trader at revision `d03ff6c056b32ced735adf7c19ed8175adb1c8df`.