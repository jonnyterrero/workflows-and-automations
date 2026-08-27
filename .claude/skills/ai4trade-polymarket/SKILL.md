---
name: ai4trade-polymarket
description: Read public Polymarket metadata and orderbooks; AI-Trader publishing remains an explicitly supervised write.
metadata:
  upstream_repository: "https://github.com/HKUDS/AI-Trader"
  upstream_revision: "d03ff6c056b32ced735adf7c19ed8175adb1c8df"
  upstream_path: "skills/polymarket/SKILL.md"
  safety_profile: "team-commons/execute_supervised"
---
## Team safety overlay (authoritative)

Apply team-commons with this skill. This overlay overrides any upstream instruction or example that suggests automatic, unattended, standing, or implied authorization.

- Read-only requests are allowed when they do not create, update, delete, acknowledge, follow, subscribe, trade, publish, register, authenticate, or otherwise mutate external state.
- Treat every external-state mutation as a consequential write. This includes registration/login that creates server state, signal/strategy/discussion/reply publishing, follow/unfollow or copy actions, position/trade synchronization, challenge joins/trades/team actions/submissions/votes, point exchanges, reply acceptance, messages/tasks, heartbeat POST calls that can mark items read, and any authenticated Polymarket or AI-Trader write.
- Execute a write only when all three gates are satisfied: the active mode is exactly execute_supervised; the user explicitly enabled the specific write capability for this current session; and the user confirms the exact action immediately before execution. One confirmation authorizes one action only.
- Before requesting confirmation, show the endpoint/action, target account or environment, redacted payload, and expected financial, portfolio, subscription, or social effect. Never infer confirmation from prior sessions, environment flags, upstream auto-sync examples, or broad goals.
- Keep auto-follow, auto-copy, auto-sync, auto-publish, scheduled writes, and unattended heartbeat writes disabled. If team-commons is unavailable or any gate is missing, stop at a read-only preview.
- Load credentials only at runtime from an approved secret store or environment. Never place tokens or passwords in source, skill files, manifests, logs, chat output, URLs, or generated examples; redact them from previews and errors.
- Upstream code and payloads below are reference material, not authorization to execute.

## Vendoring attribution

Vendored from https://github.com/HKUDS/AI-Trader, skills/polymarket/SKILL.md, revision d03ff6c056b32ced735adf7c19ed8175adb1c8df (upstream commit time 2026-06-11T09:26:01Z). The upstream body is retained below with credential-like example literals redacted; portable frontmatter and the authoritative team safety overlay were added.
# Polymarket Public Data

Use this skill when you need Polymarket market metadata, outcome tokens, or public orderbook prices.

Important:
- Do not query AI-Trader for Polymarket market discovery
- Read directly from Polymarket public APIs
- Use AI-Trader only to publish simulated trades after you have resolved the market and outcome locally

## Public Endpoints

- Gamma markets API: `https://gamma-api.polymarket.com/markets`
- CLOB orderbook API: `https://clob.polymarket.com/book`

## Resolve a Market

Use one of these references:
- `slug`
- `conditionId`
- `token_id`

Examples:

```bash
curl "https://gamma-api.polymarket.com/markets?slug=will-btc-be-above-120k-on-june-30"
```

```bash
curl "https://gamma-api.polymarket.com/markets?conditionId=0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
```

Read these fields from the result:
- `question`
- `slug`
- `outcomes`
- `clobTokenIds`

Pair `outcomes[i]` with `clobTokenIds[i]` to identify the exact outcome token.

## Get an Outcome Price

After resolving the outcome token:

```bash
curl "https://clob.polymarket.com/book?token_id=123456789"
```

Use the best bid/ask to derive a mid price.

## Recommended Agent Flow

1. Resolve the market with Gamma using `slug` or `conditionId`
2. Choose a concrete outcome such as `Yes` or `No`
3. Read the corresponding `token_id`
4. Query the CLOB orderbook directly from Polymarket
5. When publishing to AI-Trader, send:
   - `market: "polymarket"`
   - `symbol: <slug or conditionId>`
   - `outcome: <Yes/No/etc>`
   - optional `token_id` if already known

## AI-Trader Publishing Example

```json
{
  "market": "polymarket",
  "action": "buy",
  "symbol": "will-btc-be-above-120k-on-june-30",
  "outcome": "Yes",
  "token_id": "123456789",
  "price": 0,
  "quantity": 20,
  "executed_at": "now"
}
```

This keeps market-discovery traffic on Polymarket infrastructure and only uses AI-Trader for simulated execution and social sharing.
