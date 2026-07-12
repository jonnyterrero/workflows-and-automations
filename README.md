# Workflows & Automations

Personal automation hub for Claude Code, MCP integrations, plugins, research tooling, and the **Obsidian Second Brain** — a system that lets Claude use your Obsidian vault as persistent memory across sessions.

**Repo:** [jonnyterrero/workflows-and-automations](https://github.com/jonnyterrero/workflows-and-automations)  
**Nested AI helper:** [`JonnyJr/`](./JonnyJr) → [jonnyterrero/JonnyJr](https://github.com/jonnyterrero/JonnyJr)

---

## What's Inside

| Area | Path | Purpose |
|------|------|---------|
| **JonnyJr** | [`JonnyJr/`](./JonnyJr) | AI research helper — automated research, synthesis, scheduled workflows, PR creation |
| **Engineering stacks** | [`Engineering-Projects/`](./Engineering-Projects) | Engineering + app-dev tech stacks (MATLAB/Python/SQL/C++, Next.js/Flutter/Supabase) |
| **Automations** | [`7-automations/`](./7-automations) | Make.com / Second Brain chief-of-staff automations |
| **Agent setups** | [`agent-trio/`](./agent-trio), [`trading-intelligence-agent/`](./trading-intelligence-agent) | Multi-agent and trading intelligence configs |
| **Claude plugins** | `claude-*-plugin-upload/` | Packaged Claude Code plugins (ruflo, context7, mem, repomix, etc.) |
| **Claude config** | [`CLAUDE.md`](./CLAUDE.md), [`.mcp.json`](./.mcp.json) | Project-level Claude Code rules and MCP servers |

---

## Tech Stack

### Engineering
- **Languages**: MATLAB, Python, SQL, C/C++
- **Tooling**: OnShape, SolidWorks, MATLAB, KiCad, ANSYS, COMSOL, Fusion 360, and more — see [`Engineering-Projects/01_Comprehensive_TechStack`](./Engineering-Projects/01_Comprehensive_TechStack)

### Full-Stack / App Development
- **Frontend**: Next.js, React, TypeScript
- **Mobile**: Flutter
- **Database**: SQL
- **Backend/BaaS**: Firebase / Supabase

---

## JonnyJr (nested)

[`JonnyJr/`](./JonnyJr) is nested here via git subtree from [jonnyterrero/JonnyJr](https://github.com/jonnyterrero/JonnyJr). It is the AI research helper: daily/nightly research workflows, synthesis scripts, and auto-PR reporting.

```bash
# From JonnyJr/
cd JonnyJr
npm install
npm run research      # run research
npm run synthesize    # synthesize findings
npm run open-pr       # open review PR
npm test
```

Upstream sync (when JonnyJr remote history changes):

```bash
git remote add jonnyjr https://github.com/jonnyterrero/JonnyJr.git   # once
git fetch jonnyjr main
git subtree pull --prefix=JonnyJr jonnyjr main --squash
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
├── JonnyJr/                           # AI research helper (subtree → jonnyterrero/JonnyJr)
├── Engineering-Projects/              # Engineering + app dev tech stacks (subtree)
├── 7-automations/                     # Make.com and Second Brain automations
├── agent-trio/                        # Multi-agent setups
├── trading-intelligence-agent/        # Trading intelligence agent
└── claude-*-plugin-upload/            # Claude Code plugin packages
```

---

## Related

- [JonnyJr](https://github.com/jonnyterrero/JonnyJr) — standalone AI research repository
- [Obsidian Local REST API plugin](https://github.com/coddingtonbear/obsidian-local-rest-api)
- [Claude Code docs](https://docs.anthropic.com/claude-code)
- [Model Context Protocol](https://modelcontextprotocol.io)
