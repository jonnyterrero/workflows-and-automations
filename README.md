# Jonny's Workflow & Automations

Personal Claude Code setup, MCP integrations, plugins, and the **Obsidian Second Brain** — a system that lets Claude use your Obsidian vault as persistent memory across sessions.

---

## Obsidian Second Brain — Install Guide

This setup connects Claude Code to your Obsidian vault via MCP so Claude can:
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

---

## Prerequisites

- [Obsidian](https://obsidian.md) installed with a vault set up
- [Claude Code](https://docs.anthropic.com/claude-code) installed (`npm install -g @anthropic-ai/claude-code`)
- Node.js 18+

---

## Step 1 — Install the Obsidian Local REST API Plugin

This plugin exposes your vault over a local HTTPS API that Claude Code connects to via MCP.

1. Open Obsidian → **Settings → Community Plugins → Browse**
2. Search for **"Local REST API"** by coddingtonbear
3. Install and **Enable** it
4. Go to **Settings → Local REST API**
5. Note your **API Key** and **port** (default: `27124`)
6. Make sure **"Enable HTTPS"** is on

> Keep the API key safe — treat it like a password. Do not commit it to any repo.

---

## Step 2 — Add the Obsidian MCP to Claude Code

Run this in your terminal:

```bash
claude mcp add obsidian-batcave \
  --transport sse \
  https://127.0.0.1:27124/
```

Or add it manually to your `~/.claude/claude_desktop_config.json` or project `.mcp.json`:

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

---

## Step 3 — Set Up the Global CLAUDE.md

This file is read automatically by Claude Code at every session start.

Create `~/.claude/CLAUDE.md` with the following content:

```markdown
# Claude Global Config

## Session Start

At the start of every Claude Code session, if the Obsidian MCP is available:
1. Read `60-Dashboards/Claude Context Hub.md` from my Obsidian vault using the obsidian-batcave MCP tool.
2. Use it to orient around my preferences, active projects, tools, and privacy rules.
3. Do not scan the whole vault.
4. Retrieve linked notes only when directly relevant to the task.
5. Ask before reading any private area.

If the Obsidian MCP is unavailable, say so briefly and continue. Do not block the session.

## Coding Defaults

- Typed, modular, production-quality code — no tutorial scaffolding
- Direct and implementation-focused — no filler
- Flag architectural debt, risky trade-offs, and security issues proactively
- Prefer editing existing files over creating new ones
- Validate inputs at system boundaries
- Never hardcode or expose secrets, tokens, credentials, or `.env` values

## Privacy Rules

Never read without explicit instruction:
- Finance notes, habit tracker, journals, health/medical logs
- Notes tagged `#private` or `#journal`
- Files containing credentials, API keys, tokens, passwords, or `.env` content

Always ask before:
- Modifying existing vault notes
- Reading sensitive personal areas beyond Task List and Weekly To-do
- Accessing archived or migrated data

## Session End

When a session produced decisions, summaries, patterns, or next actions — offer to capture them.
Route captures per the rules in `60-Dashboards/Claude Context Hub.md`.
Do not save raw transcripts unless explicitly requested.
```

---

## Step 4 — Create the Vault Notes

Create these three notes in your Obsidian vault:

| Note | Vault Path | Purpose |
|---|---|---|
| Claude Context Hub | `60-Dashboards/Claude Context Hub.md` | Session-start orientation for Claude |
| Claude Session Capture | `50-Templates/Claude Session Capture.md` | End-of-session capture template |
| Claude Second Brain Guide | `60-Dashboards/Claude Second Brain Guide.md` | Usage guide |

Templates are in [`obsidian-second-brain/`](./obsidian-second-brain/). Copy them into the matching paths in your vault and update the "Who I Am" and "Active Projects" sections with your own info.

---

## Step 5 — Verify the Connection

Open Claude Code and run:

```
Read 60-Dashboards/Claude Context Hub.md from my Obsidian vault and confirm you can see it.
```

Claude should respond with the contents of your Context Hub. If it fails:
- Check that Obsidian is open and the Local REST API plugin is running
- Verify the API key in your MCP config
- Check the port matches (default `27124`)

---

## Daily Usage

### Start a session (Claude Code — automatic)
Claude Code reads `~/.claude/CLAUDE.md` on startup and loads your context automatically.

### Start a session (Claude.ai or other — manual)
Paste this:
```
Read 60-Dashboards/Claude Context Hub.md from my Obsidian vault to orient yourself.
```

### Search your vault
```
Search my vault for notes on [topic].
What do I have in Obsidian about [project]?
Check my task list for current priorities.
```

### Capture a session
```
Capture this session using the session capture template.
Save a summary of what we just built to 00-Inbox/.
```

### Grant private access for a session
```
You have permission to read my finance tracker this session.
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

---

## Capture Routing

| Content Type | Target Path |
|---|---|
| Architecture decisions | `20-Projects/<project>/` |
| Reusable code patterns | `30-Reference/concepts/` |
| Research & articles | `30-Reference/literature/` |
| Quick captures | `00-Inbox/` |
| School notes | `School Notes/` or `Learning Hub/` |
| Session summaries | `20-Projects/<project>/` or `00-Inbox/` |

---

## Privacy

Claude will never read the following without your explicit instruction:
- Finance notes
- Habit tracker
- Private journals or personal logs
- Health or medical notes
- Files tagged `#private`
- Any credentials, API keys, tokens, or `.env` content

---

## Repo Structure

```
.
├── README.md                          # This file
├── CLAUDE.md                          # Project-level Claude Code config
├── .mcp.json                          # MCP server configuration
├── obsidian-second-brain/             # Vault note templates
│   ├── Claude Context Hub.md
│   ├── Claude Session Capture.md
│   └── Claude Second Brain Guide.md
├── 7-automations/                     # Make.com and automation configs
├── agent-trio/                        # Multi-agent setups
└── [claude-*-plugin-upload]/          # Claude Code plugin packages
```

---

## Related

- [Obsidian Local REST API plugin](https://github.com/coddingtonbear/obsidian-local-rest-api)
- [Claude Code docs](https://docs.anthropic.com/claude-code)
- [Model Context Protocol](https://modelcontextprotocol.io)
