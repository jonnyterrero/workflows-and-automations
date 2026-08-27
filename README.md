# Workflows & Automations

Personal automation hub for Claude Code, MCP integrations, plugins, research tooling, and the **Obsidian Second Brain** — a system that lets Claude use your Obsidian vault as persistent memory across sessions.

**Repo:** [jonnyterrero/workflows-and-automations](https://github.com/jonnyterrero/workflows-and-automations)  
**Nested AI helper:** [`agents/JonnyJr/`](./agents/JonnyJr) (in-tree; standalone repo retired)

---

## What's Inside

| Area | Path | Purpose |
|------|------|---------|
| **JonnyJr** | [`agents/JonnyJr/`](./agents/JonnyJr) | AI research helper — automated research, synthesis, scheduled workflows, PR creation |
| **Engineering stacks** | [`projects/Engineering-Projects/`](./projects/Engineering-Projects) | Engineering + app-dev tech stacks (MATLAB/Python/SQL/C++, Next.js/Flutter/Supabase) |
| **Automations** | [`automations/`](./automations) | Make.com / Second Brain chief-of-staff automations |
| **Agent team** | [`agents/agent-team/`](./agents/agent-team) | Portable specialist skills + Managed Agents + Cursor export (laptop/desktop) |
| **Agent trio** | [`agents/agent-trio/`](./agents/agent-trio) | Multi-agent setup |
| **Future-drivers research** | [`agents/future-drivers-research/`](./agents/future-drivers-research) | Four-agent thematic research loop on Claude Managed Agents |
| **Trading intelligence** | [`trading/trading-intelligence-agent/`](./trading/trading-intelligence-agent) | Trading intelligence agent (FastAPI + data platform) |
| **Trading desk** | [`trading/trading-desk/`](./trading/trading-desk) | Engine-workspace stub; vendor repos stay outside this hub |
| **Pilot Engine** | [`trading/pilot-engine/`](./trading/pilot-engine) | Firebase Phase 0 ingest / validate / approval-gated execute |
| **Claude plugins** | [`plugins/`](./plugins) | Packaged Claude Code plugins (ruflo, context7, mem, repomix, AI-Trader, etc.) |
| **Content engine** | [`.claude/skills/content-engine/`](./.claude/skills/content-engine) | Repo activity → YouTube packages and written posts |
| **Content production** | [`.claude/skills/content-production/`](./.claude/skills/content-production) | ElevenLabs narration, visuals, ffmpeg assembly, YouTube metadata |
| **Portfolio policy** | [`config/public-sleeve-policy.yaml`](./config/public-sleeve-policy.yaml), [`docs/portfolio-rebalance-policy.md`](./docs/portfolio-rebalance-policy.md) | Public.com sleeve policy + weekly rebalance rules |
| **Claude config** | [`CLAUDE.md`](./CLAUDE.md), [`.mcp.json`](./.mcp.json) | Project-level Claude Code rules and MCP servers |

---

## Tech Stack

### Engineering
- **Languages**: MATLAB, Python, SQL, C/C++
- **Tooling**: OnShape, SolidWorks, MATLAB, KiCad, ANSYS, COMSOL, Fusion 360, and more — see [`projects/Engineering-Projects/01_Comprehensive_TechStack`](./projects/Engineering-Projects/01_Comprehensive_TechStack)

### Full-Stack / App Development
- **Frontend**: Next.js, React, TypeScript
- **Mobile**: Flutter
- **Database**: SQL
- **Backend/BaaS**: Firebase / Supabase

---

## JonnyJr (nested)

[`agents/JonnyJr/`](./agents/JonnyJr) lives in this repo as the AI research helper: daily/nightly research workflows, synthesis scripts, and auto-PR reporting. The standalone `jonnyterrero/JonnyJr` repo has been deleted.

```bash
# From agents/JonnyJr/
cd agents/JonnyJr
npm install
npm run research      # run research
npm run synthesize    # synthesize findings
npm run open-pr       # open review PR
npm test
```

---

## Obsidian Second Brain — Install Guide

Connect Claude Code to your Obsidian vault via MCP so Claude can:
- Read your context at the start of every session
- Search your notes on demand
- Capture decisions, patterns, and summaries back into the vault

### How It Works

```
Session Start          During Session         Session End
──────────────         ──────────────         ───────────
Claude reads           Claude searches        Claude captures
Context Hub      →     vault on demand   →    outputs back
for orientation        when you ask           into vault
```

### Prerequisites

- [Obsidian](https://obsidian.md) installed with a vault set up
- [Claude Code](https://docs.anthropic.com/claude-code) installed (`npm install -g @anthropic-ai/claude-code`)
- Node.js 18+

### Step 1 — Install the Obsidian Local REST API Plugin

1. Open Obsidian → **Settings → Community Plugins → Browse**
2. Search for **"Local REST API"** by coddingtonbear
3. Install and **Enable** it
4. Go to **Settings → Local REST API**
5. Note your **API Key** and **port** (default: `27124`)
6. Make sure **"Enable HTTPS"** is on

> Keep the API key safe — treat it like a password. Do not commit it to any repo.

### Step 2 — Add the Obsidian MCP to Claude Code

```bash
claude mcp add obsidian-batcave \
  --transport sse \
  https://127.0.0.1:27124/
```

Or add it manually to `~/.claude/claude_desktop_config.json` or project `.mcp.json`:

```json
{
  "mcpServers": {
    "obsidian-batcave": {
      "url": "https://127.0.0.1:27124/",
      "headers": {
        "Authorization": "Bearer YOUR_API_KEY_HERE"
      }
    }
  }
}
```

Replace `YOUR_API_KEY_HERE` with the key from the Obsidian plugin settings.

> **Never commit your API key.** Add `.mcp.json` to `.gitignore` if it contains secrets, or use environment variable substitution.

### Step 3 — Set Up the Global CLAUDE.md

Create `~/.claude/CLAUDE.md` with session-start rules that read `60-Dashboards/Claude Context Hub.md` from the vault, apply coding defaults, enforce privacy rules, and offer session-end captures. See the project [`CLAUDE.md`](./CLAUDE.md) and prior vault templates for the full template.

### Step 4 — Create the Vault Notes

| Note | Vault Path | Purpose |
|------|------------|---------|
| Claude Context Hub | `60-Dashboards/Claude Context Hub.md` | Session-start orientation for Claude |
| Claude Session Capture | `50-Templates/Claude Session Capture.md` | End-of-session capture template |
| Claude Second Brain Guide | `60-Dashboards/Claude Second Brain Guide.md` | Usage guide |

### Step 5 — Verify the Connection

```
Read 60-Dashboards/Claude Context Hub.md from my Obsidian vault and confirm you can see it.
```

If it fails: Obsidian open + Local REST API running, API key correct, port `27124`.

---

## Daily Usage

**Start (Claude Code):** automatic via `~/.claude/CLAUDE.md`

**Start (manual):**
```
Read 60-Dashboards/Claude Context Hub.md from my Obsidian vault to orient yourself.
```

**Search / capture:**
```
Search my vault for notes on [topic].
Capture this session using the session capture template.
```

---

## Vault Structure (PARA-inspired)

```
vault/
├── 00-Inbox/          # Quick captures, unprocessed notes
├── 10-Areas/          # Ongoing areas: Personal, School, Work
├── 20-Projects/       # Active project notes
├── 30-Reference/      # Concepts, literature, reusable knowledge
├── 40-Archive/        # Archived and migrated content
├── 50-Templates/      # Note templates (including session capture)
├── 60-Dashboards/     # Index/MOC notes (Context Hub lives here)
└── attachments/
```

### Capture Routing

| Content Type | Target Path |
|--------------|-------------|
| Architecture decisions | `20-Projects/<project>/` |
| Reusable code patterns | `30-Reference/concepts/` |
| Research & articles | `30-Reference/literature/` |
| Quick captures | `00-Inbox/` |
| School notes | `School Notes/` or `Learning Hub/` |
| Session summaries | `20-Projects/<project>/` or `00-Inbox/` |

### Privacy

Claude will never read without explicit instruction:
- Finance notes, habit tracker, journals, health/medical logs
- Notes tagged `#private` or `#journal`
- Credentials, API keys, tokens, or `.env` content

---

## Repo Structure

```
.
├── README.md                          # This file
├── CLAUDE.md                          # Project-level Claude Code config
├── .mcp.json                          # MCP server configuration
├── .claude/                           # Claude Code project skills, agents, hooks
├── plugins/                           # Claude Code plugin upload bundles
├── agents/
│   ├── JonnyJr/                       # AI research helper (in-tree)
│   ├── agent-team/                    # Portable specialist skills + Managed Agents
│   ├── agent-trio/                    # Multi-agent setups
│   └── future-drivers-research/       # Thematic research loop
├── trading/
│   ├── trading-intelligence-agent/    # Trading intelligence platform
│   ├── trading-desk/                  # Engine-workspace stub
│   └── pilot-engine/                  # Firebase Phase 0
├── automations/                       # Make.com and Second Brain automations
├── projects/Engineering-Projects/     # Engineering + app dev tech stacks
├── config/                            # Sleeve / operating policy
├── docs/                              # Hub handoffs and portfolio policy
└── scripts/                           # Utility scripts (including trading-desk clones)
```

---

## Related

- [Obsidian Local REST API plugin](https://github.com/coddingtonbear/obsidian-local-rest-api)
- [Claude Code docs](https://docs.anthropic.com/claude-code)
- [Model Context Protocol](https://modelcontextprotocol.io)
